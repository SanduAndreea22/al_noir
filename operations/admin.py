from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from core.models import SiteSettings
from .models import Event, Expense, Invoice, LoyaltyAccount, LoyaltyRedemption, LoyaltyTransaction, PromoCode, Sale, StaffProfile, StaffShift, StockItem, StockMovement, Ticket, WaitlistEntry


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit', 'minimum_quantity', 'expiry_date', 'is_perishable', 'is_complimentary')
    list_filter = ('is_perishable', 'is_complimentary')
    search_fields = ('name', 'supplier')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('item', 'movement_type', 'quantity', 'note', 'created_at')
    list_filter = ('movement_type', 'created_at')
    readonly_fields = ('created_at',)
    def has_change_permission(self, request, obj=None): return False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'customer', 'quantity', 'unit_price', 'payment_method', 'created_at')
    list_filter = ('payment_method', 'created_at')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'category', 'amount', 'expense_date', 'paid')
    list_filter = ('category', 'paid', 'expense_date')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'starts_at', 'ticket_price', 'capacity', 'is_active')
    list_filter = ('is_active', 'requires_reservation')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('event', 'customer_name', 'quantity', 'paid', 'created_at')
    list_filter = ('paid', 'event')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'customer_name', 'amount', 'issued_at', 'paid')
    list_filter = ('paid', 'issued_at')
    search_fields = ('number', 'customer_name', 'customer_email')


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'available_rewards', 'updated_at')
    search_fields = ('user__username', 'user__email')


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'points', 'note', 'created_at')
    readonly_fields = ('account', 'points', 'note', 'created_at')
    def has_change_permission(self, request, obj=None): return False


@admin.register(LoyaltyRedemption)
class LoyaltyRedemptionAdmin(admin.ModelAdmin):
    list_display = ('code', 'account', 'reward', 'used_at', 'created_at')
    list_filter = ('used_at',)
    search_fields = ('code', 'account__user__username')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'uses', 'max_uses', 'is_active', 'active_until')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


@admin.register(StaffShift)
class StaffShiftAdmin(admin.ModelAdmin):
    list_display = ('staff', 'starts_at', 'ends_at', 'clocked_in_at', 'clocked_out_at')
    list_filter = ('staff__role',)


@admin.action(description='Send availability notification')
def notify_waitlist(modeladmin, request, queryset):
    site_settings = SiteSettings.objects.first()
    restaurant_name = site_settings.restaurant_name if site_settings else 'us'
    for entry in queryset.filter(status=WaitlistEntry.WAITING):
        send_mail(
            'A table might be available',
            f'Hi {entry.name}! A table may now be available for the waitlist request you made for '
            f'{entry.reservation_date}. Please contact {restaurant_name} to confirm.',
            settings.DEFAULT_FROM_EMAIL, [entry.email], fail_silently=True,
        )
        entry.status = WaitlistEntry.NOTIFIED
        entry.save(update_fields=('status',))


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ('name', 'reservation_date', 'reservation_time', 'guests', 'status', 'created_at')
    list_filter = ('status', 'reservation_date')
    search_fields = ('name', 'email', 'phone')
    actions = (notify_waitlist,)
