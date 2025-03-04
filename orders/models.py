from django.db import models
from django.contrib.auth.models import User
from product.models import Product
import datetime
from django.utils import timezone
from utils.generate_code import generate_code

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

    
    



ORDER_STATUS = [
    ('Received','Received'),
    ('Processed','Processed'),
    ('Shipped','Shipped'),
    ('Delivered','Delivered')
]

class Order(models.Model):
    user = models.ForeignKey(User,related_name='order_user',on_delete=models.SET_NULL,null=True,blank=True)
    status = models.CharField(max_length=10,choices=ORDER_STATUS , default='Received')
    code = models.CharField(max_length=20,default=generate_code())
    order_time = models.DateTimeField(default=timezone.now)
    delivery_time = models.DateTimeField(null=True,blank=True)
    coupon = models.ForeignKey('Coupon',related_name='order_coupon',on_delete=models.SET_NULL,null=True,blank=True)
    total_After_coupon = models.FloatField(null=True,blank=True)
    #tracking mpesa payment 
    mpesa_checkout_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')  # pending, completed, failed
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    payment_phone = models.CharField(max_length=15, null=True, blank=True)
    
    def __str__(self):
        return str(self.user)
    




class OrderDetail(models.Model):
    order = models.ForeignKey(Order, related_name='order_detail', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_product', on_delete=models.SET_NULL, null=True, blank=True)
    price = models.FloatField()
    quantity = models.IntegerField()
    total = models.FloatField(null=True, blank=True)  # Ensure this field exists and is calculated

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity  # Calculate total as price * quantity
        super(OrderDetail, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.order)

    




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