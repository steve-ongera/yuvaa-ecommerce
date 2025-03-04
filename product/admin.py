from django.contrib import admin
from .models import Product , ProductImages ,Brand ,Review ,ShoeSize , PickupStation
from django.utils.text import slugify

# Register your models here.

class ProductImagesTabular(admin.TabularInline):
    model = ProductImages




class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'flag', 'price', 'quantity', 'brand', 'slug']
    list_filter = ['flag', 'brand']
    search_fields = ['name', 'subtitle', 'description']
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug in admin
    inlines = [ProductImagesTabular]
    ordering = ['name']  # Sort products alphabetically

    def save_model(self, request, obj, form, change):
        """Ensure slug uniqueness when saving a product."""
        if not obj.slug:
            base_slug = slugify(obj.name)
            unique_slug = base_slug
            num = 1
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            obj.slug = unique_slug
        super().save_model(request, obj, form, change)


admin.site.register(Product,ProductAdmin)
admin.site.register(ProductImages)
admin.site.register(Brand)
admin.site.register(Review)
admin.site.register(ShoeSize)
admin.site.register(PickupStation)
