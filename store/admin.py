from django.contrib import admin
from .models import Category, Order, OrderItem, Product, Profile, ProductImage

# --- 1. SETUP FOR EXTRA IMAGES ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Shows 3 empty slots for uploading photos by default

# --- 2. CATEGORY ADMIN ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

# --- 3. PRODUCT ADMIN (WITH EXTRA IMAGES) ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active', 'is_trending', 'category']
    list_filter = ['is_active', 'is_trending', 'category']
    list_editable = ['price', 'is_active', 'is_trending']
    inlines = [ProductImageInline]  # <--- THIS ADDS THE GALLERY UPLOADER!

# --- 4. ORDER ADMIN ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'price', 'quantity']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]
    search_fields = ['order_id', 'user__username', 'phone']

# --- 5. PROFILE ADMIN ---
admin.site.register(Profile)