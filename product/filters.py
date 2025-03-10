
from django_filters import rest_framework as filters
from .models import Product

class ProductFilter(filters.FilterSet):
    # Price filters
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    
    # Tag filters
    new_items = filters.BooleanFilter(field_name="is_new")
    sale_items = filters.BooleanFilter(field_name="on_sale")
    rating_items = filters.BooleanFilter(method='filter_by_rating')
    feature_items = filters.BooleanFilter(field_name="is_featured")
    discount_items = filters.BooleanFilter(field_name="has_discount")
    
    # Category filters
    categories = filters.CharFilter(method='filter_by_categories')
    
    # Brand filters
    brands = filters.CharFilter(method='filter_by_brands')
    
    def filter_by_rating(self, queryset, name, value):
        # Filter products with rating above a threshold (e.g., 4.0)
        if value:
            return queryset.filter(avg_rate__gte=4.0)
        return queryset
    
    def filter_by_categories(self, queryset, name, value):
        if value:
            category_ids = value.split(',')
            return queryset.filter(category__id__in=category_ids)
        return queryset
    
    def filter_by_brands(self, queryset, name, value):
        if value:
            brand_ids = value.split(',')
            return queryset.filter(brand__id__in=brand_ids)
        return queryset
    
    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'new_items', 'sale_items', 
                 'rating_items', 'feature_items', 'discount_items', 
                 'categories', 'brands']