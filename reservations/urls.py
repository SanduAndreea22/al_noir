from django.urls import path

from . import views


app_name = "reservations"


urlpatterns = [

    path(
        "",
        views.reservations,
        name="reservations",
    ),
    path('checkout/<int:pk>/<str:token>/', views.checkout, name='checkout'),
    path('payment-success/<int:pk>/', views.payment_success, name='payment_success'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),

]
