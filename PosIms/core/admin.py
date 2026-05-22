from django.contrib import admin
from .models import User, Customer, Product, Sale, SaleItem, Return
from .models import Purchase
from .models import Supplier


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role',)
    search_fields = ('username', 'email')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'created_at')
    search_fields = ('name', 'phone_number')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'selling_price', 'purchase_price', 'stock_quantity', 'purchase_type', 'supplier')
    search_fields = ('name', 'category')
    list_filter = ('category', 'purchase_type', 'supplier')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'cashier', 'total_amount', 'timestamp')
    list_filter = ('timestamp',)


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'price_at_sale', 'discount_amount')


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'return_amount', 'returned_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'sale__id')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'purchase_type', 'credit_by', 'total_amount', 'timestamp')
    list_filter = ('purchase_type', 'timestamp')
    search_fields = ('supplier', 'credit_by__username')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'created_at')
    search_fields = ('name',)
