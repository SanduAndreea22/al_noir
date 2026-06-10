from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'reservation_date',
        'reservation_time',
        'guests',
        'status',
    )

    list_filter = (
        'status',
        'reservation_date',
    )

    search_fields = (
        'name',
        'email',
        'phone',
    )

    filter_horizontal = (
        'selected_items',
    )