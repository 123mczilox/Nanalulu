from django.contrib import admin
from .models import Category, Store, Brand, Product, ProductImage, ProductVariant


# Register your models here.
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(ProductImage)
# admin.site.register(ProductVariant)



class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "store",
        "is_featured",
        "is_active",
    )

    list_filter = (
        "brand",
        "category",
        "is_featured",
        "is_active",
    )

    search_fields = (
        "name",
        "brand__name",
        "category__name",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    inlines = [ProductVariantInline]

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'county', 'is_active',)
    list_filter = ('is_active', 'county','name')
    search_fields = ('is_active', 'county', 'name', 'phone_number', 'email','county')
