# filters.py
import django_filters
from .models import Product, Brand, Category

class ProductFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    brands = django_filters.ModelMultipleChoiceFilter(
        field_name='brand',
        queryset=Brand.objects.all(),
        method='filter_brands'
    )
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name='category',
        queryset=Category.objects.all(),
        method='filter_categories'
    )

    class Meta:
        model = Product
        fields = ['name', 'price_min', 'price_max', 'brands', 'categories']
    
    def filter_brands(self, queryset, name, value):
        if value:
            brand_ids = [brand.id for brand in value]
            return queryset.filter(brand__id__in=brand_ids)
        return queryset
    
    def filter_categories(self, queryset, name, value):
        if value:
            category_ids = [category.id for category in value]
            return queryset.filter(category__id__in=category_ids)
        return queryset