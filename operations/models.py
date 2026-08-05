from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone
from menu.models import MenuItem


class StockItem(models.Model):
    name = models.CharField(max_length=150, unique=True)
    unit = models.CharField(max_length=20, default='buc')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    expiry_date = models.DateField(null=True, blank=True)
    is_perishable = models.BooleanField(default=False)
    is_complimentary = models.BooleanField(default=False)
    supplier = models.CharField(max_length=150, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    @property
    def is_low_stock(self):
        return self.quantity < self.minimum_quantity

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < timezone.localdate())

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    PURCHASE, SALE, WASTE, ADJUSTMENT = 'purchase', 'sale', 'waste', 'adjustment'
    TYPES = [(PURCHASE, 'Aprovizionare'), (SALE, 'Vânzare'), (WASTE, 'Pierdere/expirat'), (ADJUSTMENT, 'Ajustare')]
    item = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('Mișcările de stoc nu se editează; creează o ajustare nouă.')
        delta = self.quantity if self.movement_type in (self.PURCHASE, self.ADJUSTMENT) else -self.quantity
        with transaction.atomic():
            item = StockItem.objects.select_for_update().get(pk=self.item_id)
            item.quantity += delta
            item.save(update_fields=['quantity', 'updated_at'])
            super().save(*args, **kwargs)


class Sale(models.Model):
    CASH, CARD, ONLINE = 'cash', 'card', 'online'
    PAYMENT_METHODS = [(CASH, 'Numerar'), (CARD, 'Card'), (ONLINE, 'Online')]
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name='sales')
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    stock_item = models.ForeignKey(StockItem, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default=CARD)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating and not self.unit_price:
            self.unit_price = self.menu_item.price
        if creating and not self.stock_item_id and self.menu_item.stock_item_id:
            self.stock_item = self.menu_item.stock_item
        super().save(*args, **kwargs)
        if creating and self.stock_item_id:
            StockMovement.objects.create(item=self.stock_item, movement_type=StockMovement.SALE, quantity=self.quantity, note=f'Vânzare #{self.pk}')
        if creating and self.customer_id:
            points = int(self.total)
            if points:
                LoyaltyAccount.objects.get_or_create(user=self.customer)[0].add_points(points, f'Vânzare #{self.pk}')


class Expense(models.Model):
    SUPPLIER, SALARY, OTHER = 'supplier', 'salary', 'other'
    CATEGORIES = [(SUPPLIER, 'Furnizor'), (SALARY, 'Salariu'), (OTHER, 'Diverse')]
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField(default=timezone.localdate)
    paid = models.BooleanField(default=True)
    supplier = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ('-expense_date',)

    def __str__(self):
        return self.description


class Event(models.Model):
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=0, help_text='0 înseamnă nelimitat')
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    requires_reservation = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('starts_at',)

    @property
    def is_free(self):
        return self.ticket_price == Decimal('0')

    def __str__(self):
        return self.title


class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    quantity = models.PositiveIntegerField(default=1)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.event} – {self.customer_name}'


class Invoice(models.Model):
    number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField(blank=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_at = models.DateField(default=timezone.localdate)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ('-issued_at', '-id')

    def __str__(self):
        return self.number


class LoyaltyAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_account')
    points = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_rewards(self):
        return self.points // 100

    def add_points(self, amount, note=''):
        self.points = models.F('points') + amount
        self.save(update_fields=('points', 'updated_at'))
        self.refresh_from_db(fields=('points', 'updated_at'))
        LoyaltyTransaction.objects.create(account=self, points=amount, note=note)

    def __str__(self):
        return f'{self.user} – {self.points} puncte'


class LoyaltyTransaction(models.Model):
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    points = models.IntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)


class LoyaltyRedemption(models.Model):
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.PROTECT, related_name='redemptions')
    code = models.CharField(max_length=20, unique=True)
    reward = models.ForeignKey(MenuItem, on_delete=models.PROTECT, limit_choices_to={'is_loyalty_reward': True})
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_used(self):
        return self.used_at is not None

    def __str__(self):
        return self.code


class PromoCode(models.Model):
    PERCENT, FIXED, FREE_ITEM = 'percent', 'fixed', 'free_item'
    TYPES = [(PERCENT, 'Reducere procentuală'), (FIXED, 'Reducere fixă'), (FREE_ITEM, 'Produs gratuit')]
    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=12, choices=TYPES, default=PERCENT)
    value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    free_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True)
    active_from = models.DateTimeField(default=timezone.now)
    active_until = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    uses = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.active_from <= now and (not self.active_until or self.active_until >= now) and (self.max_uses is None or self.uses < self.max_uses)

    def discount_for(self, amount):
        if self.discount_type == self.PERCENT:
            return (amount * self.value / Decimal('100')).quantize(Decimal('0.01'))
        if self.discount_type == self.FIXED:
            return min(amount, self.value)
        return Decimal('0')

    def register_use(self):
        self.uses = models.F('uses') + 1
        self.save(update_fields=('uses',))
        self.refresh_from_db(fields=('uses',))

    def __str__(self):
        return self.code


class StaffProfile(models.Model):
    CEO, MANAGER, WAITER, KITCHEN = 'ceo', 'manager', 'waiter', 'kitchen'
    ROLES = [(CEO, 'CEO'), (MANAGER, 'Manager'), (WAITER, 'Ospătar'), (KITCHEN, 'Bucătărie / Bar')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=20, choices=ROLES, default=WAITER)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} – {self.get_role_display()}'


class StaffShift(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='shifts')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    clocked_in_at = models.DateTimeField(null=True, blank=True)
    clocked_out_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ('-starts_at',)

    def __str__(self):
        return f'{self.staff} – {self.starts_at:%d.%m %H:%M}'


class WaitlistEntry(models.Model):
    WAITING, NOTIFIED, CONVERTED, CANCELLED = 'waiting', 'notified', 'converted', 'cancelled'
    STATUSES = [(WAITING, 'În așteptare'), (NOTIFIED, 'Notificat'), (CONVERTED, 'Rezervare creată'), (CANCELLED, 'Anulat')]
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    guests = models.PositiveSmallIntegerField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default=WAITING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('reservation_date', 'reservation_time', 'created_at')

    def __str__(self):
        return f'{self.name} – {self.reservation_date} {self.reservation_time}'
