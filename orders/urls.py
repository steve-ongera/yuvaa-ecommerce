from django.urls import path
from .views import OrderList , checkout ,add_to_cart , remove_from_cart, update_pickup_station , pay_view ,order_success ,transaction_list ,transaction_detail 
from . import views
from .api import CartDetailCreateAPI , OrderListAPI , OrderDetailAPI , CreateOrderAPI , ApplyCouponAPI 



app_name = 'orders'

urlpatterns = [
    path('', OrderList.as_view()),
    path('checkout', checkout , name="checkout" ),
    path('add_to_cart', add_to_cart ,name ='add_to_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update-cart'),
    path('<int:id>/remove-from-cart',remove_from_cart),
    path('update-pickup-station/', update_pickup_station, name='update_pickup_station'),

   

    # Payment URLs
    path('pay/', views.pay_view, name='pay'),
    path('check-status/<int:transaction_id>/', views.check_transaction_status, name='check_transaction_status'),
    path('order-success/', views.order_success, name='order_success'),
    
    # M-Pesa Callback URL (must be publicly accessible - no login required)
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),


    path('transactions/', transaction_list, name='transaction_list'),
    path('transactions/<str:transaction_id>/', transaction_detail, name='transaction_detail'),

    path('mpesa/validation/', views.mpesa_validation, name='mpesa_validation'),
    path('mpesa/confirmation/', views.mpesa_confirmation, name='mpesa_confirmation'),
   
    # api  
    path('api/list/<str:username>',OrderListAPI.as_view()),
    path('api/list/<str:username>/create-order',CreateOrderAPI.as_view()),
    path('api/<str:username>/cart', CartDetailCreateAPI.as_view()),
    path('api/<str:username>/cart/apply-coupon', ApplyCouponAPI.as_view()),
    path('api/list/<str:username>/<int:pk>',OrderDetailAPI.as_view()),
]
