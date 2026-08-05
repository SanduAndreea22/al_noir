from django.urls import path
from . import views
app_name = 'operations'
urlpatterns = [path('events/', views.events, name='events'), path('events/<int:pk>/book/', views.event_booking, name='event_booking'), path('waitlist/', views.waitlist, name='waitlist'), path('client/', views.client_dashboard, name='client_dashboard'), path('loyalty/redeem/', views.redeem_reward, name='redeem_reward'), path('staff/', views.staff_dashboard, name='staff_dashboard'), path('staff/reports/', views.reports, name='reports'), path('staff/schedule/', views.staff_schedule, name='staff_schedule'), path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf')]
