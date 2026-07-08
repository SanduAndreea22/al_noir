from django.contrib import admin

from .models import Reservation, Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):

    list_display = (
        "number",
        "capacity",
        "status",
    )

    list_filter = (
        "capacity",
        "status",
    )

    search_fields = (
        "number",
    )

    ordering = (
        "number",
    )


@admin.action(description="Confirm selected reservations")
def confirm_reservations(modeladmin, request, queryset):
    queryset.update(status="confirmed")


@admin.action(description="Cancel selected reservations")
def cancel_reservations(modeladmin, request, queryset):
    queryset.update(status="cancelled")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "reservation_date",
        "reservation_time",
        "guests",
        "table",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "reservation_date",
        "table",
    )

    search_fields = (
        "name",
        "email",
        "phone",
    )

    filter_horizontal = (
        "selected_items",
    )

    actions = (
        confirm_reservations,
        cancel_reservations,
    )

    ordering = (
        "-reservation_date",
        "-reservation_time",
    )