from django.db import models
from django.contrib.auth.models import User 
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from django.utils.text import slugify
from django.db.models.aggregates import Avg
from django.db.models import Avg
from decimal import Decimal

from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
 
    
    @property
    def get_full_path(self):
        """Return the full category path (including parent categories)"""
        if self.parent:
            return f"{self.parent.get_full_path} > {self.name}"
        return self.name
    
    @property
    def has_children(self):
        """Check if category has child categories"""
        return self.children.exists()
    
    @property
    def get_all_children(self):
        """Get all descendant categories recursively"""
        children = list(self.children.all())
        for child in list(children):
            children.extend(child.get_all_children)
        return children

class PickupStation(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    details = models.TextField()
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2 , null= True , blank=True)
    
    def __str__(self):
        return self.name

class ShoeSize(models.Model):
    size = models.CharField(_('Size'), max_length=5)  # e.g., "7", "8", "9", "10"
    
    def __str__(self):
        return self.size

from django.utils.text import slugify

# Create your models here.
FLAG_TYPES =[
    ('Sale','Sale'),
    ('New','New'),
    ('Feature','Feature'),
]

class Product(models.Model):
    name = models.CharField(_('Name'),max_length=120)
    flag = models.CharField(_('Flag'),max_length=10,choices=FLAG_TYPES)
    image = models.ImageField(_('Image'),upload_to='products')
    price = models.FloatField(_('Price'))
    sku = models.CharField(_('SKU'),max_length=12)
    subtitle = models.CharField(_('Subtitle'),max_length=300)
    description = models.TextField(_('Description'),max_length=40000)
    quantity = models.IntegerField(_('Quantity'))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_products' , null=True , blank=True)
    brand = models.ForeignKey('Brand',verbose_name=_('Brand'), related_name='product_brand', on_delete=models.SET_NULL, null=True)
    tags = TaggableManager()
    slug = models.SlugField(null=True , blank=True , unique=True )

    available_sizes = models.ManyToManyField(ShoeSize,  blank=True)

    order_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0 , null=True , blank=True)
    discount = models.FloatField(default=0.0 , null=True , blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2 , null=True , blank=True)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2 , null=True , blank=True)

    def __str__(self):
        return self.name
    
    # instance method = each object ,self=object
    def avg_rate(self):
        avg = self.review_product.aggregate(rate_avg=Avg('rate'))
        if not avg['rate_avg'] :
            result = 0
            return result
        return avg['rate_avg']


    def save(self, *args, **kwargs):
        if not self.slug:  # Only generate slug if empty
            base_slug = slugify(self.name)  # Convert name to a slug
            slug = base_slug
            counter = 1
            
            # Ensure the slug is unique by appending a number if needed
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

         # Auto-calculate discounted price
        if self.original_price and self.discount:
            discount_decimal = Decimal(self.discount)  # Convert discount to Decimal
            self.discounted_price = self.original_price * (Decimal(1) - (discount_decimal / Decimal(100)))
        else:
            self.discounted_price = self.original_price  # If no discount, keep original price

        super().save(*args, **kwargs)  # Call the original save() method


class ProductImages(models.Model):
    product = models.ForeignKey(Product ,verbose_name=_('Product'), related_name='product_image', on_delete=models.CASCADE)
    image = models.ImageField(_('Image'),upload_to='product_images')
    def __str__(self):
        return str(self.product)
    



class Brand(models.Model):
    name = models.CharField(_('Name'),max_length=100)
    image = models.ImageField(_('Image'),upload_to='brand')
    slug = models.SlugField(null=True , blank=True)

    def __str__(self):
        return self.name
    

    def save(self, *args, **kwargs):
       self.slug = slugify(self.name) 
       super(Brand, self).save(*args, **kwargs) # Call the real save() method




class Review(models.Model):
    user = models.ForeignKey(User,verbose_name=_('User'), related_name='review_author', on_delete=models.SET_NULL , null=True)
    product = models.ForeignKey(Product,verbose_name=_('Product'), related_name='review_product', on_delete=models.CASCADE)
    rate = models.IntegerField(_('Rate'))
    review = models.CharField(_('Review'),max_length=300)
    created_at = models.DateField(_('Created at'),default=timezone.now)

    def __str__(self):
        return f"{self.user} - {self.product}" 
    




