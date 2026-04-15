from django.contrib import admin
from .models import SiteSettings, ContactMessage, Review

admin.site.register(SiteSettings)
admin.site.register(ContactMessage)
admin.site.register(Review)
