from django.urls import path
from .views import home, about, reviews, contact, privacy, terms, register
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('reviews/', reviews, name='reviews'),
    path('contact/', contact, name='contact'),
    path('privacy/', privacy, name='privacy'),
    path('terms/', terms, name='terms'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
