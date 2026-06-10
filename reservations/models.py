from django.db import models


class Reservation(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)

    reservation_date = models.DateField()
    reservation_time = models.TimeField()

    guests = models.PositiveIntegerField()

    selected_items = models.ManyToManyField(
        'menu.MenuItem',
        blank=True
    )

    special_request = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.reservation_date}"
        )