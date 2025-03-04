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
    
    cart, created = Cart.objects.get_or_create(user=request.user, status='InProgress')
    
    cart_detail, created = CartDetail.objects.get_or_create(cart=cart, product=product , size=size)
    cart_detail.quantity = quantity
    cart_detail.total = round(quantity * product.price, 2)
    cart_detail.save()
    
    # Add success message
    messages.success(request, f'{product.name} has been added to your cart!')

    return redirect(f'/products/{product.slug}')



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


def order_summary(request):
    # Retrieve the user's active cart
    cart = get_object_or_404(Cart, user=request.user, status="InProgress")
    
    # Get or create an order associated with the cart
    order, created = Order.objects.get_or_create(
        user=request.user, 
        status='Received',
        defaults={'total_After_coupon': cart.total_After_coupon or cart.cart_total()}
    )
    
    # Get all cart details (products in the cart)
    cart_details = cart.cart_detail.all()
    
    # Calculate the total price before and after applying the coupon
    total_before_coupon = cart.cart_total()
    total_after_coupon = cart.total_After_coupon if cart.total_After_coupon else total_before_coupon
    
    # Prepare context for the template
    context = {
        'cart': cart,
        'order': order,  # Include the order object in the context
        'cart_details': cart_details,
        'total_before_coupon': total_before_coupon,
        'total_after_coupon': total_after_coupon,
    }
    return render(request, 'orders/order_summary.html', context)



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


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product table
    cart_items = Cart.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = Order()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = Cart.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = Order.objects.get(id=orderproduct.id)
        orderproduct.save()


        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    Cart.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    mail_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)



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



#mpesa integration
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Order
from .utils import lipa_na_mpesa_online
import json

def mpesa_initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Calculate total including any discounts
    order_total = order.total_After_coupon if order.total_After_coupon else sum(detail.total for detail in order.order_detail.all())

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        # Format phone number to include country code if needed
        if not phone_number.startswith('254'):
            phone_number = '254' + phone_number.lstrip('0')
        
        account_reference = f'Order_{order.code}'
        transaction_desc = f'Payment for order {order.code}'
        
        # Add print statements for debugging
        print(f"Phone Number: {phone_number}")
        print(f"Amount: {order_total}")
        print(f"Reference: {account_reference}")
        
        response = lipa_na_mpesa_online(
            phone_number=phone_number,
            amount=order_total,
            reference=account_reference,
            description=transaction_desc
        )
        
        # Print the full response for debugging
        print("M-Pesa API Response:", response)
        
        if response.get('ResponseCode') == '0':
            order.status = 'Processed'
            # Update order with checkout details
            order.mpesa_checkout_id = response.get('CheckoutRequestID')
            order.payment_status = 'pending'
            order.payment_phone = phone_number
            order.save()
            
            request.session['mpesa_checkout_id'] = response.get('CheckoutRequestID')
            request.session['order_id'] = order_id
            
            return render(request, 'orders/mpesa_loading.html', {'checkout_id': response.get('CheckoutRequestID')})
        
        # Return the actual error message from M-Pesa
        return JsonResponse({
            'status': 'error',
            'message': response.get('ResponseDescription', 'Payment initiation failed'),
            'details': response  # Include full response for debugging
        }, status=400)
    
    return render(request, 'orders/mpesa.html', {
        'order': order,
        'total': order_total
    })

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            callback_data = json.loads(request.body)
            result = callback_data.get('Body', {}).get('stkCallback', {})
            
            checkout_request_id = result.get('CheckoutRequestID')
            result_code = result.get('ResultCode')
            result_desc = result.get('ResultDesc')
            
            # Find the order using the checkout request ID from the session
            try:
                order = Order.objects.get(code=checkout_request_id)
                
                if result_code == "0":
                    # Payment successful
                    order.payment_status = 'completed'
                    order.status = 'Processed'

                    # Extract MpesaReceiptNumber from callback metadata
                    if 'CallbackMetadata' in result:
                        metadata = result['CallbackMetadata']['Item']
                        for item in metadata:
                            if item['Name'] == 'MpesaReceiptNumber':
                                order.mpesa_receipt_number = item['Value']
                    
                    # If you want to store transaction details
                    # if 'CallbackMetadata' in result:
                    #     metadata = result['CallbackMetadata']['Item']
                    #     for item in metadata:
                    #         if item['Name'] == 'MpesaReceiptNumber':
                    #             order.payment_id = item['Value']
                    #         elif item['Name'] == 'Amount':
                    #             order.amount_paid = str(item['Value'])
                            
                else:
                    # Payment failed
                    order.status = 'Received'  # Reset to initial status
                
                order.save()
                
                return JsonResponse({'status': 'success'})
                
            except Order.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Order not found'
                }, status=404)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON payload'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

def check_transaction_status(request, checkout_request_id):
    try:
        order = Order.objects.get(mpesa_checkout_id=checkout_request_id)
        return JsonResponse({
            'status': order.payment_status,
            'receipt_number': order.mpesa_receipt_number
        })
    except Order.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found'
        }, status=404)
    

def mpesa_payment_success(request):
    return render(request, 'orders/mpesa_payment_success.html')

def mpesa_payment_failed(request):
    return render(request, 'orders/mpesa_payment_failed.html')