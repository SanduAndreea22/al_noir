from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu, name='menu'),
    path('favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
    path('rate/<int:pk>/', views.rate_item, name='rate_item'),
]