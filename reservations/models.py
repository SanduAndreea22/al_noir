from django.db import models


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

    name = models.CharField(max_length=150)

    email = models.EmailField()

    phone = models.CharField(max_length=30)

    reservation_date = models.DateField()

    reservation_time = models.TimeField()

    guests = models.PositiveSmallIntegerField()

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

    def __str__(self):
        return (
            f"{self.name} | "
            f"{self.reservation_date} "
            f"{self.reservation_time}"
        )