from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Contact)
admin.site.register(Favorite)
admin.site.register(ProductsImage)
@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'productname', 'productprice', 'category')
admin.site.register(Review)
@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity')
admin.site.register(Customer)
@admin.register(OrderPlaced)
class OrderPlacedModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'customer', 'product', 'quantity')