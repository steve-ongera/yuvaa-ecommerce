from rest_framework import serializers
from django.db.models.aggregates import Avg
from taggit.serializers import TagListSerializerField , TaggitSerializer
from .models import Product ,Brand ,Review
from django.db.models import Q, Avg
from rest_framework import generics

class ProductListSerializer(serializers.ModelSerializer):
#  brand = BrandListSerializer()
    brand = serializers.StringRelatedField()
    avg_rate = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
#    price_with_tax = serializers.SerializerMethodField()
    class Meta :
        model = Product
        fields = '__all__'

# def get_price_with_tax(self,product):
    #    return product.price*1.5
    
    def get_avg_rate(self,product):
        avg = product.review_product.aggregate(rate_avg=Avg('rate'))
        if not avg['rate_avg'] :
            result = 0
            return result
        return avg['rate_avg']

    def get_reviews_count(self,product:Product):
        reviews = product.review_product.all().count()
        return reviews 


from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import ProductListSerializer
from .filters import ProductFilter
from .models import Product, Category, Brand
from django.db.models import Count

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    


def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    
    # Get all categories with product count
    context['categories'] = Category.objects.annotate(
        product_count=Count('product')
    ).order_by('name')
    
    # Get all brands with product count
    context['brands'] = Brand.objects.annotate(
        product_count=Count('product')
    ).order_by('name')
    
    # Get selected category IDs
    selected_categories = self.request.GET.get('categories', '')
    if selected_categories:
        context['selected_category_ids'] = [int(id) for id in selected_categories.split(',')]
    else:
        context['selected_category_ids'] = []
    
    # Get selected brand IDs
    selected_brands = self.request.GET.get('brands', '')
    if selected_brands:
        context['selected_brand_ids'] = [int(id) for id in selected_brands.split(',')]
    else:
        context['selected_brand_ids'] = []
    
    return context


class ReviewsSerializer(serializers.ModelSerializer):
    class Meta :
        model = Review
        fields = '__all__'

class ProductDetailSerializer(TaggitSerializer,serializers.ModelSerializer):
    brand = serializers.StringRelatedField()
    avg_rate = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    reviews = ReviewsSerializer(source='review_product' , many=True)
    tags = TagListSerializerField()
    class Meta :
        model = Product
        fields = '__all__'


    def get_avg_rate(self,product):
        avg = product.review_product.aggregate(rate_avg=Avg('rate'))
        if not avg['rate_avg'] :
            result = 0
            return result
        return avg['rate_avg']

    def get_reviews_count(self,product:Product):
        reviews = product.review_product.all().count()
        return reviews 


class BrandListSerializer(serializers.ModelSerializer):
    class Meta :
        model = Brand
        fields = '__all__'


class BrandDetailSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(source='product_brand',many=True)
    class Meta :
        model = Brand
        fields = '__all__'



class ProductCartSerializer(serializers.ModelSerializer):
    class Meta :
        model = Product
        fields = ['name' , 'image' , 'price']