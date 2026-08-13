import secrets

from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import User


def generate_access_token():
    return secrets.token_urlsafe(32)


class Table(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("inactive", "Inactive"),
    ]

    number = models.PositiveIntegerField(unique=True)

    capacity = models.PositiveSmallIntegerField(
        choices=[
            (2, "2 Persons"),
            (4, "4 Persons"),
            (6, "6 Persons"),
            (10, "10 Persons"),
        ]
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
    )

    class Meta:
        ordering = ["number"]
        verbose_name = "Table"
        verbose_name_plural = "Tables"

    def __str__(self):
        return f"Table {self.number} ({self.capacity} persons)"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations")

    name = models.CharField(max_length=150)

    email = models.EmailField()

    phone = models.CharField(max_length=30)

    reservation_date = models.DateField()

    reservation_time = models.TimeField()

    guests = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    selected_items = models.ManyToManyField(
        "menu.MenuItem",
        blank=True,
        related_name="reservations",
    )

    special_request = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    advance_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    advance_paid = models.BooleanField(default=False)
    access_token = models.CharField(max_length=43, default=generate_access_token, editable=False, unique=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)
    promo_code = models.CharField(max_length=40, blank=True)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    promo_free_item = models.ForeignKey(
        'menu.MenuItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='promo_reservations'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-reservation_date",
            "-reservation_time",
        ]
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        constraints = [
            models.UniqueConstraint(
                fields=["table", "reservation_date", "reservation_time"],
                condition=models.Q(status__in=["pending", "confirmed"]),
                name="unique_active_table_slot",
            ),
        ]

    def __str__(self):
        return (
            f"{self.name} | "
            f"{self.reservation_date} "
            f"{self.reservation_time}"
        )
