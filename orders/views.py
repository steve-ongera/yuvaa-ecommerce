from django.shortcuts import render , redirect
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order ,Cart , CartDetail,OrderDetail , Coupon
from product.models import Product , PickupStation
from django.shortcuts import get_object_or_404
from settings.models import DeliveryFee
import datetime
from django.contrib import messages
from django.utils.timezone import now
from datetime import timedelta
from django.http import JsonResponse
from django.template.loader import render_to_string
from accounts.models import Profile


from django.views.decorators.http import require_POST
import json

class OrderList(LoginRequiredMixin,ListView):
    model = Order
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        return queryset
    



@login_required(login_url='/accounts/login/')  # Redirect to login if not authenticated
def add_to_cart(request):
    quantity = int(request.POST['quantity'])
    product = get_object_or_404(Product, id=request.POST['product_id'])

    size = request.POST.get('size')  # Get selected size

    if not size:
        messages.error(request, "Please select a shoe size.")
        return redirect(f'/products/{product.slug}')
    
    # Check available quantity
    if quantity > product.quantity:  # Using `quantity` instead of `stock`
        messages.error(request, f"Only {product.quantity} items available in stock.")
        return redirect(f'/products/{product.slug}')
    
    cart, created = Cart.objects.get_or_create(user=request.user, status='InProgress')
    
    cart_detail, created = CartDetail.objects.get_or_create(cart=cart, product=product, size=size)
    
    # Ensure the total quantity in the cart does not exceed available quantity
    new_quantity = cart_detail.quantity + quantity if not created else quantity
    if new_quantity > product.quantity:
        messages.error(request, f"Only {product.quantity} items available in stock.")
        return redirect(f'/products/{product.slug}')
    
    cart_detail.quantity = new_quantity
    cart_detail.total = round(new_quantity * product.price, 2)
    cart_detail.save()
    
    messages.success(request, f'{product.name} has been added to your cart!')

    return redirect(f'/products/{product.slug}')


def update_cart(request, item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_quantity = int(data.get('quantity'))
            
            # Get the cart detail item
            cart_detail = get_object_or_404(CartDetail, id=item_id)
            
            # Check if we have enough stock
            if new_quantity > cart_detail.product.quantity:
                return JsonResponse({
                    'success': False, 
                    'message': f'Only {cart_detail.product.quantity} items available in stock.'
                }, status=400)
            
            # Update the quantity and recalculate total
            cart_detail.quantity = new_quantity
            cart_detail.total = round(new_quantity * cart_detail.product.price, 2)
            cart_detail.save()
            
            # Calculate the new cart total
            cart = cart_detail.cart
            from django.db.models import Sum
            cart_total = CartDetail.objects.filter(cart=cart).aggregate(
                cart_total=Sum('total')
            )['cart_total'] or 0
            
            # Return updated cart information
            return JsonResponse({
                'success': True, 
                'message': 'Cart updated',
                'new_quantity': new_quantity,
                'new_total': cart_detail.total,
                'cart_total': round(cart_total, 2)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


def remove_from_cart(request,id):
    cart_detail = CartDetail.objects.get(id=id)
    cart_detail.delete()
    return redirect('/products/')



@login_required
def checkout(request):
    user = request.user
    
    try:
        # Get the user's active cart
        cart = Cart.objects.get(user=user, status='InProgress')
        cart_detail = CartDetail.objects.filter(cart=cart)

        # Calculate cart total and total items
        cart_total = float(cart.cart_total() or 0.0)  # Ensure cart_total is always a float
        cart_total_items = sum(item.quantity for item in cart_detail)

        # Ensure an order exists or create a new one
        order, created = Order.objects.get_or_create(
            user=user, 
            status='pending',
            defaults={'total_price': cart_total}
        )

        # Get or create a default pickup station
        pickup_station, station_created = PickupStation.objects.get_or_create(
            name="G4S Nairobi-Kenol Station",
            defaults={
                'location': 'Nairobi, Java House',
                'details': 'Nairobi, Java House, Ground Floor, Nairobi - Kenol',
                'delivery_fee': DeliveryFee.objects.last().fee if DeliveryFee.objects.last() else 0.0  # Ensure delivery_fee exists
            }
        )

        # Update order with pickup station and delivery fee
        order.pickup_station = pickup_station
        order.delivery_fee = float(pickup_station.delivery_fee or 0.0)  # Ensure delivery_fee is always a float

        # Calculate total price including delivery fee
        order.total_price = cart_total + order.delivery_fee
        order.save()


        # Move cart items to order items
        for cart_item in cart_detail:
            OrderDetail.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,  # Store price at the time of order
                total=cart_item.product.price * cart_item.quantity , # Calculate total price per item
                 size=cart_item.size
            )

        # Calculate delivery date (3-2 days after order but not on weekends)
        def calculate_delivery_date(order_date):
            delivery_date = order_date + timedelta(days=2)  # Default to 2 days after

            if delivery_date.weekday() in [5, 6]:  # If Saturday (5) or Sunday (6)
                delivery_date += timedelta(days=(7 - delivery_date.weekday()))  # Move to Monday

            return delivery_date.strftime('%d %B')  # Format as "DD Month"

        # Assign delivery date
        order_date = datetime.date.today()  # Get current date
        delivery_start_date = calculate_delivery_date(order_date)
        delivery_end_date = calculate_delivery_date(order_date + timedelta(days=1))  # One day after

        # Coupon handling (if POST request)
        coupon = None
        if request.method == 'POST':
            try:
                coupon = get_object_or_404(Coupon, code=request.POST['coupon_code'])
                
                # Check coupon validity
                today_date = datetime.today().date()  # Corrected
                if coupon.quantity > 0 and coupon.start_date <= today_date <= coupon.end_date:
                    # Calculate coupon discount
                    coupon_value = cart_total * (coupon.discount / 100)
                    discounted_cart_total = cart_total - coupon_value

                    # Update coupon and cart
                    coupon.quantity -= 1
                    coupon.save()
                    
                    cart.coupon = coupon
                    cart.total_After_coupon = discounted_cart_total
                    cart.save()

            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code")


        # Fetch the user's profile and shipping address (with error handling)
        profile, created = Profile.objects.get_or_create(user=user)
        shipping_address = getattr(profile, 'shipping_address', None)
    
   

        #Prepare context for template
        context = {
            'cart_detail': cart_detail,
            'sub_total': cart_total,
            'cart_total': cart_total + order.delivery_fee,
            'coupon': coupon,
            'delivery_fee': order.delivery_fee,
            'cart_total_items': cart_total_items,
            'user': user,
            'delivery_start_date': delivery_start_date,
            'delivery_end_date': delivery_end_date,
            'pickup_station': order.pickup_station,
            'pickup_stations': PickupStation.objects.all(),
            'shipping_address': shipping_address  # Pass the shipping address to the template
        
        }

        return render(request, 'orders/checkout2.html', context)

    except Cart.DoesNotExist:
        messages.error(request, "No active cart found.")
        return redirect('/')  # Redirect to cart page
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('/')  # Redirect to home page




@login_required
@require_POST
def update_pickup_station(request):
    try:
        data = json.loads(request.body)
        station_id = data.get('station_id')
        
        # Extensive logging
        print(f"Received station_id: {station_id}")
        
        user = request.user
        
        # Get the user's cart with detailed logging
        try:
            cart = Cart.objects.get(user=user, status='InProgress')
            print(f"Cart found: {cart.id}")
            print(f"Cart Total: {cart.cart_total()}")
        except Cart.DoesNotExist:
            print("No active cart found!")
            return JsonResponse({
                'success': False, 
                'error': 'No active cart found'
            })
        
        # Get the user's pending order with detailed logging
        try:
            order = Order.objects.get(user=user, status='pending')
            print(f"Order found: {order.id}")
        except Order.DoesNotExist:
            print("No pending order found!")
            return JsonResponse({
                'success': False, 
                'error': 'No pending order found'
            })
        
        # Get the pickup station with detailed logging
        try:
            pickup_station = get_object_or_404(PickupStation, id=station_id)
            print(f"Pickup Station: {pickup_station.name}")
            print(f"Delivery Fee: {pickup_station.delivery_fee}")
        except Exception as e:
            print(f"Error finding pickup station: {e}")
            return JsonResponse({
                'success': False, 
                'error': 'Pickup station not found'
            })
        
        # Update order details
        order.pickup_station = pickup_station
        order.delivery_fee = float(pickup_station.delivery_fee or 0.0)
        
        # Calculate totals
        cart_total = float(cart.cart_total() or 0.0)
        order_total = cart_total + order.delivery_fee

        print(f"Cart Total: {cart_total}")
        print(f"Delivery Fee: {order.delivery_fee}")
        print(f"Order Total: {order_total}")

        # Save the order
        order.total_price = order_total
        order.save()

        return JsonResponse({
            'success': True,
            'station_name': pickup_station.name,
            'station_details': pickup_station.details,
            'new_delivery_fee': order.delivery_fee,  
            'order_total': order_total,
            'cart_total': cart_total,
        })
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, Transaction, Cart, CartDetail, Product
from decimal import Decimal

@login_required
def backup_pay_view(request):
    user = request.user

    # Retrieve the user's active cart
    cart = get_object_or_404(Cart, user=user, status="InProgress")

    # Retrieve cart details (products in the cart)
    cart_details = cart.cart_detail.all()

    # Validate stock before proceeding
    for item in cart_details:
        product = item.product
        if product.quantity < item.quantity:
            messages.error(request, f"Not enough stock for {product.name}. Available: {product.quantity}")
            return redirect('orders:checkout')  # Redirect user to cart page

    # Get or create an order associated with the cart
    order, created = Order.objects.get_or_create(
        user=user, 
        status='pending',
        defaults={
            'total_After_coupon': cart.total_After_coupon or cart.cart_total(),
            'total_price': cart.total_After_coupon or cart.cart_total(),  # Ensure total_price is updated
        }
    )

    # Fetch delivery fee (If not set, default to 0)
    delivery_fee = order.delivery_fee if order.delivery_fee else 0.00

    # Calculate total prices
    total_before_coupon = cart.cart_total()
    total_after_coupon = cart.total_After_coupon if cart.total_After_coupon else total_before_coupon

    # Final total including delivery fee
    final_total = Decimal(total_after_coupon) + delivery_fee  

    if request.method == "POST":
        name = request.POST.get("name")
        id_number = request.POST.get("id_number")
        phone_number = request.POST.get("phone_number")

        if not all([name, id_number, phone_number]):
            messages.error(request, "All fields are required.")
            return redirect('pay')

        # Create a transaction with the correct total
        transaction = Transaction.objects.create(
            user=user,
            order=order,
            name=name,
            id_number=id_number,
            phone_number=phone_number,
            amount=final_total,  # ✅ Ensure the total includes the delivery fee
            status="completed",
            pickup_station=order.pickup_station
        )

        # Update order status and total price
        order.status = 'completed'
        order.total_price = final_total  # ✅ Update total_price with delivery fee included
        order.save()

        # Reduce stock for each product in the cart
        for item in cart_details:
            product = item.product
            product.quantity -= item.quantity
            product.save()

        # Clear the cart
        cart.cart_detail.all().delete()
        cart.status = "Completed"
        cart.save()

        messages.success(request, "Payment successful! Your order has been placed.")
        return redirect('orders:order_success')

    # Prepare context for rendering the template
    context = {
        "cart": cart,
        "order": order,
        "cart_details": cart_details,
        "total_before_coupon": total_before_coupon,
        "total_after_coupon": total_after_coupon,
        "delivery_fee": delivery_fee,  # ✅ Pass delivery fee to the template
        "final_total": final_total,  # ✅ Pass final total including delivery fee
    }

    return render(request, "orders/pay.html", context)



def order_success(request):
    return render(request, 'orders/order_success.html')



#mpesa integrations
#  Add callback views to handle M-Pesa responses

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .mpesa import initiate_stk_push, register_c2b_urls
from .models import Transaction, Order



@csrf_exempt
def mpesa_validation(request):
    """
    Validation URL for C2B API - called when a customer enters your paybill number
    """
    # For paybill, you can validate the account number (e.g., check if order exists)
    if request.method == 'POST':
        try:
            # Parse JSON from M-Pesa
            mpesa_data = json.loads(request.body)
            account_number = mpesa_data.get('BillRefNumber')
            
            # Check if the order code exists and is still pending
            if account_number and Order.objects.filter(code=account_number, payment_status='pending').exists():
                # Valid order, accept the payment
                return JsonResponse({
                    "ResultCode": 0,
                    "ResultDesc": "Accepted"
                })
            
            # Invalid account/order, reject the payment
            return JsonResponse({
                "ResultCode": 1,
                "ResultDesc": "Rejected"
            })
            
        except Exception as e:
            # Log error and reject
            print(f"Validation error: {str(e)}")
            return JsonResponse({
                "ResultCode": 1,
                "ResultDesc": "Rejected due to error"
            })
    
    return HttpResponse(status=400)



@csrf_exempt
def mpesa_confirmation(request):
    """
    Confirmation URL for C2B API - called after successful payment
    """
    if request.method == 'POST':
        try:
            # Parse JSON from M-Pesa
            mpesa_data = json.loads(request.body)
            
            # Extract payment details
            transaction_id = mpesa_data.get('TransID')
            transaction_time = mpesa_data.get('TransTime')
            amount = mpesa_data.get('TransAmount')
            account_number = mpesa_data.get('BillRefNumber')  # Should match order `code`
            phone_number = mpesa_data.get('MSISDN')
            
            # Find the order using `code` instead of `id`
            try:
                order = Order.objects.get(code=account_number, payment_status='pending')
                
                # Create or update transaction
                transaction, created = Transaction.objects.get_or_create(
                    order=order,
                    defaults={
                        'user': order.user,
                        'name': order.user.get_full_name() or 'Customer',
                        'phone_number': phone_number,
                        'amount': amount,
                        'status': 'completed',
                        'mpesa_receipt_number': transaction_id,
                    }
                )
                
                if not created:
                    transaction.status = 'completed'
                    transaction.mpesa_receipt_number = transaction_id
                    transaction.save()
                
                # Update order payment status
                order.payment_status = 'completed'
                order.mpesa_receipt_number = transaction_id
                order.payment_phone = phone_number
                order.save()
                
                # Update product quantities and cart status
                try:
                    cart = Cart.objects.get(user=order.user, status="InProgress")
                    for item in cart.cart_detail.all():
                        product = item.product
                        product.quantity -= item.quantity
                        product.save()
                    
                    # Clear the cart
                    cart.cart_detail.all().delete()
                    cart.status = "Completed"
                    cart.save()
                except Cart.DoesNotExist:
                    print(f"No active cart found for user {order.user}")

            except Order.DoesNotExist:
                print(f"Payment received for non-existent order: {account_number}")

            # Always return success to M-Pesa
            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Success"
            })
            
        except Exception as e:
            # Log error but still return success to M-Pesa
            print(f"Confirmation error: {str(e)}")
            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Success with errors"
            })
    
    return HttpResponse(status=400)


import json
import requests
import base64
from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db import transaction
from .models import Cart, Order, Transaction, OrderDetail, MpesaPayment

# M-Pesa Configuration from .env
MPESA_CONSUMER_KEY = getattr(settings, 'MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
MPESA_SHORTCODE = getattr(settings, 'MPESA_SHORTCODE', '')
MPESA_PASSKEY = getattr(settings, 'MPESA_PASSKEY', '')
MPESA_CALLBACK_URL = getattr(settings, 'MPESA_CALLBACK_URL', '')
MPESA_API_URL = getattr(settings, 'MPESA_API_URL', 'https://sandbox.safaricom.co.ke')


def get_mpesa_access_token():
    """Generate M-Pesa access token"""
    try:
        auth_url = f'{MPESA_API_URL}/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(
            auth_url,
            auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET),
            timeout=30
        )
        response.raise_for_status()
        token = response.json().get('access_token')
        print(f"✅ Access token obtained: {token[:20]}...")
        return token
    except Exception as e:
        print(f"❌ Error getting access token: {str(e)}")
        return None


def format_phone_number(phone):
    """Format phone number to 254XXXXXXXXX"""
    phone = phone.strip().replace(' ', '').replace('-', '')
    
    if phone.startswith('+254'):
        return phone[1:]
    elif phone.startswith('254'):
        return phone
    elif phone.startswith('0'):
        return '254' + phone[1:]
    elif phone.startswith('7') or phone.startswith('1'):
        return '254' + phone
    else:
        return '254' + phone


def initiate_mpesa_stk_push(phone_number, amount, account_reference, transaction_desc):
    """Initiate M-Pesa STK Push"""
    access_token = get_mpesa_access_token()
    if not access_token:
        return {
            'success': False,
            'error': 'Failed to get M-Pesa access token'
        }

    # Format phone number
    phone_number = format_phone_number(phone_number)
    print(f"📱 Formatted phone: {phone_number}")

    # Generate timestamp and password
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password_str = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode('utf-8')

    # Prepare STK Push payload
    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)),
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    print(f"🚀 Initiating STK Push...")
    print(f"   Amount: KES {amount}")
    print(f"   Phone: {phone_number}")
    print(f"   Reference: {account_reference}")
    print(f"   Callback: {MPESA_CALLBACK_URL}")

    try:
        stk_url = f'{MPESA_API_URL}/mpesa/stkpush/v1/processrequest'
        response = requests.post(
            stk_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        result = response.json()
        print(f"📥 M-Pesa Response: {json.dumps(result, indent=2)}")

        if response.status_code == 200 and result.get('ResponseCode') == '0':
            return {
                'success': True,
                'checkout_request_id': result.get('CheckoutRequestID'),
                'merchant_request_id': result.get('MerchantRequestID'),
                'response_description': result.get('ResponseDescription')
            }
        else:
            return {
                'success': False,
                'error': result.get('errorMessage', result.get('ResponseDescription', 'STK Push failed'))
            }
            
    except requests.exceptions.RequestException as e:
        print(f"❌ STK Push request error: {str(e)}")
        return {
            'success': False,
            'error': f'Connection error: {str(e)}'
        }
    except Exception as e:
        print(f"❌ STK Push error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@login_required
def pay_view(request):
    """Single payment view handling both form display and M-Pesa payment"""
    user = request.user

    # Retrieve the user's active cart
    cart = get_object_or_404(Cart, user=user, status="InProgress")
    cart_details = cart.cart_detail.all()

    # Validate stock
    for item in cart_details:
        product = item.product
        if product.quantity < item.quantity:
            messages.error(request, f"Not enough stock for {product.name}. Available: {product.quantity}")
            return redirect('orders:checkout')

    # Get or create order
    order, created = Order.objects.get_or_create(
        user=user, 
        status='Received',
        defaults={
            'code': f"ORD{user.id}{cart.id}",  
            'total_After_coupon': cart.total_After_coupon or cart.cart_total(),
            'total_price': cart.total_After_coupon or cart.cart_total(),  
        }
    )

    # Calculate totals
    delivery_fee = order.delivery_fee if order.delivery_fee else Decimal('0.00')
    total_before_coupon = cart.cart_total()
    total_after_coupon = cart.total_After_coupon if cart.total_After_coupon else total_before_coupon
    final_total = Decimal(total_after_coupon) + delivery_fee

    # Handle AJAX request for M-Pesa payment
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        name = request.POST.get("name")
        id_number = request.POST.get("id_number")
        phone_number = request.POST.get("phone_number")

        print(f"\n{'='*50}")
        print(f"💳 Payment Request Received")
        print(f"{'='*50}")
        print(f"Name: {name}")
        print(f"ID: {id_number}")
        print(f"Phone: {phone_number}")
        print(f"Amount: KES {final_total}")
        print(f"{'='*50}\n")

        if not all([name, id_number, phone_number]):
            return JsonResponse({
                'success': False,
                'error': 'All fields are required.'
            })

        # Check for existing pending transaction
        existing_transaction = Transaction.objects.filter(
            order=order, 
            status="pending"
        ).first()
        
        if existing_transaction:
            return JsonResponse({
                'success': False,
                'error': 'A payment is already in progress. Please wait or refresh the page.'
            })

        # Create transaction
        try:
            trans = Transaction.objects.create(
                user=user,
                order=order,
                name=name,
                id_number=id_number,
                phone_number=phone_number,
                amount=final_total,
                status="pending",
                pickup_station=order.pickup_station
            )
            print(f"✅ Transaction created: ID {trans.id}")
        except Exception as e:
            print(f"❌ Error creating transaction: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Error creating transaction: {str(e)}'
            })

        # Initiate M-Pesa STK Push
        mpesa_result = initiate_mpesa_stk_push(
            phone_number=phone_number,
            amount=final_total,
            account_reference=order.code,
            transaction_desc=f"Payment for Order {order.code}"
        )

        if mpesa_result['success']:
            # Store checkout request ID
            trans.checkout_request_id = mpesa_result['checkout_request_id']
            trans.save()

            # Create MpesaPayment record
            MpesaPayment.objects.create(
                phone_number=phone_number,
                amount=final_total,
                reference=order.code,
                description=f"Payment for Order {order.code}",
                checkout_request_id=mpesa_result['checkout_request_id'],
                status='PENDING'
            )

            print(f"✅ STK Push sent successfully")
            print(f"   CheckoutRequestID: {mpesa_result['checkout_request_id']}")
            
            return JsonResponse({
                'success': True,
                'message': 'STK Push sent! Please check your phone and enter M-Pesa PIN.',
                'transaction_id': trans.id,
                'checkout_request_id': mpesa_result['checkout_request_id']
            })
        else:
            # Failed to initiate
            trans.status = 'failed'
            trans.save()
            
            print(f"❌ STK Push failed: {mpesa_result.get('error')}")
            
            return JsonResponse({
                'success': False,
                'error': mpesa_result.get('error', 'Failed to initiate payment')
            })

    # Regular GET request - show form
    context = {
        "cart": cart,
        "order": order,
        "cart_details": cart_details,
        "total_before_coupon": total_before_coupon,
        "total_after_coupon": total_after_coupon,
        "delivery_fee": delivery_fee,
        "final_total": final_total,
    }

    return render(request, "orders/pay.html", context)


@login_required
@require_http_methods(["GET"])
def check_transaction_status(request, transaction_id):
    """Check transaction payment status via AJAX"""
    try:
        trans = Transaction.objects.get(
            id=transaction_id,
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'status': trans.status,
            'mpesa_receipt_number': trans.mpesa_receipt_number or ''
        })
        
    except Transaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transaction not found'
        })


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """Handle M-Pesa payment callback"""
    try:
        callback_data = json.loads(request.body)
        
        print(f"\n{'='*50}")
        print(f"📨 M-Pesa Callback Received")
        print(f"{'='*50}")
        print(json.dumps(callback_data, indent=2))
        print(f"{'='*50}\n")
        
        # Extract callback body
        body = callback_data.get('Body', {}).get('stkCallback', {})
        checkout_request_id = body.get('CheckoutRequestID')
        result_code = body.get('ResultCode')
        result_desc = body.get('ResultDesc')
        
        print(f"🔍 Processing callback:")
        print(f"   CheckoutRequestID: {checkout_request_id}")
        print(f"   ResultCode: {result_code}")
        print(f"   ResultDesc: {result_desc}")
        
        # Find transaction
        try:
            trans = Transaction.objects.get(
                checkout_request_id=checkout_request_id
            )
            print(f"✅ Transaction found: ID {trans.id}")
        except Transaction.DoesNotExist:
            print(f"❌ Transaction not found for CheckoutRequestID: {checkout_request_id}")
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Success'
            })
        
        if result_code == 0:
            # Payment successful
            print(f"✅ Payment successful!")
            
            # Extract metadata
            callback_metadata = body.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt = None
            phone_number = None
            amount_paid = None
            
            for item in callback_metadata:
                name = item.get('Name')
                if name == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
                elif name == 'PhoneNumber':
                    phone_number = item.get('Value')
                elif name == 'Amount':
                    amount_paid = item.get('Value')
            
            print(f"   Receipt: {mpesa_receipt}")
            print(f"   Phone: {phone_number}")
            print(f"   Amount: {amount_paid}")
            
            # Update transaction and order atomically
            with transaction.atomic():
                trans.status = 'completed'
                trans.mpesa_receipt_number = mpesa_receipt
                trans.save()
                
                order = trans.order
                order.payment_status = 'completed'
                order.mpesa_receipt_number = mpesa_receipt
                order.mpesa_checkout_id = checkout_request_id
                order.payment_phone = phone_number
                order.save()
                
                # Update MpesaPayment record
                mpesa_payment = MpesaPayment.objects.filter(
                    checkout_request_id=checkout_request_id
                ).first()
                
                if mpesa_payment:
                    mpesa_payment.status = 'COMPLETED'
                    mpesa_payment.receipt_number = mpesa_receipt
                    mpesa_payment.transaction_id = mpesa_receipt
                    mpesa_payment.save()
                
                # Create order details from cart
                cart = Cart.objects.filter(
                    user=order.user, 
                    status='InProgress'
                ).first()
                
                if cart:
                    for cart_item in cart.cart_detail.all():
                        # Create order detail
                        OrderDetail.objects.create(
                            order=order,
                            product=cart_item.product,
                            price=cart_item.product.price,
                            quantity=cart_item.quantity,
                            total=cart_item.total,
                            size=cart_item.size
                        )
                        
                        # Update product stock
                        product = cart_item.product
                        product.quantity -= cart_item.quantity
                        product.save()
                        
                        print(f"   ✅ Product {product.name}: Stock updated ({product.quantity} remaining)")
                    
                    # Mark cart as completed
                    cart.status = 'Completed'
                    cart.save()
                    print(f"   ✅ Cart marked as completed")
            
            print(f"✅ Order {order.code} processed successfully!\n")
            
        else:
            # Payment failed
            print(f"❌ Payment failed: {result_desc}")
            
            trans.status = 'failed'
            trans.save()
            
            order = trans.order
            order.payment_status = 'failed'
            order.save()
            
            # Update MpesaPayment record
            mpesa_payment = MpesaPayment.objects.filter(
                checkout_request_id=checkout_request_id
            ).first()
            
            if mpesa_payment:
                mpesa_payment.status = 'FAILED'
                mpesa_payment.save()
        
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Success'
        })
        
    except Exception as e:
        print(f"❌ Callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': str(e)
        })


@login_required
def order_success(request):
    """Order success page"""
    return render(request, 'orders/order_success.html')

#e-commerce admin view 
@login_required
def transaction_list(request):
    """View to display all transactions"""
    # For staff/admin users, show all transactions
    if request.user.is_staff:
        transactions = Transaction.objects.all().order_by('-timestamp')
    # For regular users, show only their transactions
    else:
        transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    
    context = {
        'transactions': transactions,
    }
    return render(request, 'orders/transaction_list.html', context)

@login_required
def transaction_detail(request, transaction_id):
    """View to display details of a specific transaction"""
    if request.user.is_staff:
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    else:
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    
    order = transaction.order  # Get the associated order
    order_items = OrderDetail.objects.filter(order=order)  # Fix: Fetch order items correctly

    context = {
        'transaction': transaction,
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'orders/transaction_detail.html', context)


import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import base64
from django.http import HttpResponse, JsonResponse
import datetime
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import *




from orders.models import Order

def create_order_from_cart(user, cart):
    if cart.cart_detail.exists():
        total = cart.cart_total()
        order = Order.objects.create(
            user=user,
            status="Received",
            total_After_coupon=cart.total_After_coupon or total,
        )
        # Transfer cart details to order details
        for item in cart.cart_detail.all():
            OrderDetail.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity,
                total=item.total,
            )
        return order
    return None


