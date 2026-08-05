from django.contrib import admin
from .models import Category, MenuItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_item', 'is_available', 'is_loyalty_reward')
    list_filter = ('category', 'is_available', 'is_loyalty_reward')
    autocomplete_fields = ('stock_item',)
