from django_filters import rest_framework as filters
from .models import CustomerProfile, ProductCatalog

class CustomerProfileFilter(filters.FilterSet):
    is_email_verified = filters.BooleanFilter()
    
    class Meta:
        model = CustomerProfile
        fields = ['is_email_verified', 'role']
        

class ProductCatalogFilter(filters.FilterSet):
    product_name = filters.CharFilter(
        field_name="product_name",
        lookup_expr="icontains"   # or icontains
    )
    
    class Meta:
        model = ProductCatalog
        fields = [
            'product_name',
            'category',
            'product_rating'
        ]