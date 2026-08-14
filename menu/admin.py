from django.contrib import admin
from .models import Category, Favorite, MenuItem, Rating


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_item', 'is_available', 'is_loyalty_reward')
    list_filter = ('category', 'is_available', 'is_loyalty_reward')
    autocomplete_fields = ('stock_item',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'item__name')


@admin.action(description='Approve selected ratings')
def approve_ratings(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'stars', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'stars')
    search_fields = ('item__name', 'user__username')
    actions = (approve_ratings,)
