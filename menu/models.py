from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_available = models.BooleanField(default=True)
    is_loyalty_reward = models.BooleanField(
        default=False,
        help_text='Can be offered as a free dessert through the loyalty program.'
    )
    stock_item = models.ForeignKey(
        'operations.StockItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='menu_items',
        help_text="If set, this item's stock decreases automatically with every sale."
    )

    def __str__(self):
        return f"{self.name} - {self.category.name}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_items')
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user} ♥ {self.item}'


class Rating(models.Model):
    STARS_CHOICES = [(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')]

    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='menu_ratings')
    stars = models.PositiveSmallIntegerField(choices=STARS_CHOICES)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('item', 'user')
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.item} - {self.stars}★ by {self.user}'
