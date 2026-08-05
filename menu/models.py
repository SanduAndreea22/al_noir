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
        help_text='Poate fi oferit ca desert gratuit prin programul de loialitate.'
    )
    stock_item = models.ForeignKey(
        'operations.StockItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='menu_items',
        help_text='Dacă e setat, stocul acestui produs scade automat la fiecare vânzare.'
    )

    def __str__(self):
        return f"{self.name} - {self.category.name}"
