from django.db import models
from django.contrib.auth.models import User
from product.models import Product , PickupStation
import datetime
from django.utils import timezone
from utils.generate_code import generate_code
import random
import string
from django.db import models
from django.utils import timezone
from datetime import timedelta, date

CART_STATUS = [
    ('InProgress' , 'InProgress'),
    ('Completed' , 'Completed'),
]

class Cart(models.Model):
    user = models.ForeignKey(User,related_name='cart_user',on_delete=models.SET_NULL,null=True,blank=True)
    status = models.CharField(max_length=10,choices=CART_STATUS)
    coupon = models.ForeignKey('Coupon',related_name='cart_coupon',on_delete=models.SET_NULL,null=True,blank=True)
    total_After_coupon = models.FloatField(null=True,blank=True)

    def __str__(self):
        return str(self.user)
    
    def cart_total(self):
        total = 0
        for item in self.cart_detail.all():
            total += item.total

        return total 




class CartDetail(models.Model):
    cart = models.ForeignKey(Cart,related_name='cart_detail',on_delete=models.CASCADE)
    product = models.ForeignKey(Product,related_name='cart_product',on_delete=models.SET_NULL,null=True,blank=True)
    quantity = models.IntegerField(default=1)
    total = models.FloatField(null=True,blank=True)

    size = models.CharField(max_length=10, null=True, blank=True)  # Store size as a string

    def __str__(self):
        return f"{self.cart} : {self.product.name} - Size: {self.size}"

    
    

import uuid

ORDER_STATUS = [
    ('Received','Received'),
    ('Processed','Processed'),
    ('Shipped','Shipped'),
    ('Delivered','Delivered')
]

class Order(models.Model):
    user = models.ForeignKey(User,related_name='order_user',on_delete=models.SET_NULL,null=True,blank=True)
    status = models.CharField(max_length=10,choices=ORDER_STATUS , default='Received')
    code = models.CharField(max_length=20, unique=True, blank=True)  # ✅ CORRECT
    order_time = models.DateTimeField(default=timezone.now)
    delivery_time = models.DateTimeField(null=True,blank=True)
    coupon = models.ForeignKey('Coupon',related_name='order_coupon',on_delete=models.SET_NULL,null=True,blank=True)
    total_After_coupon = models.FloatField(null=True,blank=True)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Ensure this field exists

    #new fields 
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pickup_station = models.ForeignKey(PickupStation, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_start_date = models.DateField(null=True, blank=True)
    delivery_end_date = models.DateField(null=True, blank=True)

    #tracking mpesa payment 
    mpesa_checkout_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')  # pending, completed, failed
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    payment_phone = models.CharField(max_length=15, null=True, blank=True)


    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                new_code = str(uuid.uuid4())[:8]  # Generate a unique 8-character code
                if not Order.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break  # Ensure the generated code is unique
        super(Order, self).save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.code} - {self.user}'
    




class OrderDetail(models.Model):
    order = models.ForeignKey(Order, related_name='order_detail', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_product', on_delete=models.SET_NULL, null=True, blank=True)
    price = models.FloatField()
    quantity = models.IntegerField()
    total = models.FloatField(null=True, blank=True)  # Ensure this field exists and is calculated

    def __str__(self):
        return str(self.order)
    




class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    pickup_station = models.ForeignKey(PickupStation, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_id = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Match Order's code field

    def save(self, *args, **kwargs):
        """ Ensure transaction_id is set to the order's code when saving """
        if not self.transaction_id and self.order:
            self.transaction_id = self.order.code  # Set transaction_id to order code
        super().save(*args, **kwargs)

    def get_order_items_display(self):
        items = self.order.order_detail.all()  # Use the correct related name
        if not items:
            return "No items"
        
        item_strings = [f"{item.quantity} x {item.product.name}" for item in items if item.product]
        return ", ".join(item_strings)


    def __str__(self):
        items_summary = self.get_order_items_display()
        return f"Transaction {self.transaction_id} - {self.user.username} ({items_summary})"


    




class Coupon(models.Model):
    code = models.CharField(max_length=20)
    discount = models.IntegerField()
    quantity = models.IntegerField()
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True,blank=True)

    def __str__(self):
        return self.code 
    
    # def save(self, *args, **kwargs):
    #     week = datetime.timedelta(days=7)
    #     self.end_date = self.start_date + week
    #     super(ModelName, self).save(*args, **kwargs) # Call the real save() method


    def save(self, *args, **kwargs):
        week = datetime.timedelta(days=7)
        self.end_date = self.start_date + week
        super(Coupon, self).save(*args, **kwargs)


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100) # this is the total amount paid
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id