from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from utils.generate_code import generate_code
# Create your models here.
from orders.models import PickupStation  # Assuming PickupStation model exists and has the address field

class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile', null=True, blank=True)
    code = models.CharField(max_length=10, default=generate_code)
    first_name = models.CharField(max_length=15, null=True, blank=True)
    last_name = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    
    # ForeignKey to PickupStation (one-to-many relationship)
    shipping_address = models.ForeignKey(PickupStation, null=True, blank=True, on_delete=models.SET_NULL)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)  # Payment method field

    def __str__(self):
        return f'{self.user.username} Profile'


# Signal to set default shipping address and payment method after profile is saved
@receiver(post_save, sender=Profile)
def set_default_shipping_and_payment(sender, instance, created, **kwargs):
    if created:  # Only run this logic when a new profile is created
        # Set default payment method to 'mpesa' if not already set
        if not instance.payment_method:
            instance.payment_method = 'mpesa'

        # Set default pickup station (shipping address) to the first PickupStation related to the user
        if not instance.shipping_address:
            try:
                # Fetch the first PickupStation related to the user (assuming it has an address field)
                # Assuming the PickupStation model is related to User in some way, 
                # e.g. PickupStation.objects.filter(user=instance.user).first()
                station = PickupStation.objects.first()  # Modify this line if there's a relationship
                if station:
                    instance.shipping_address = station  # Set the first station as the default PickupStation
            except PickupStation.DoesNotExist:
                pass  # If no PickupStation is found, shipping_address remains null

        instance.save()  # Save the instance with the updated fields


@receiver(post_save,sender=User)
def create_profile(sender,instance,created,**kwargs):
    if created :
        Profile.objects.create(
            user = instance
        )




ADDRESS_TYPES = (
    ('Home','Home'),
    ('Business','Business'),
    ('Office','Office'),
    ('Academy','Academy'),
    ('Other','Other'),
)

class Address(models.Model):
    user = models.ForeignKey(User,related_name='user_address', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=ADDRESS_TYPES)
    address = models.TextField(max_length=300)
    notes = models.TextField(null=True,blank=True)



PHONE_TYPES = (
    ('Primary','Primary'),
    ('Secondary','Secondary'),
)

class Phone(models.Model):
    user = models.ForeignKey(User,related_name='user_phone', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=PHONE_TYPES)
    phone = models.CharField(max_length=25)