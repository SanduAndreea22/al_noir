from django.contrib import admin
from .models import SiteSettings, ContactMessage, Review

admin.site.site_header = 'Al Noir'
admin.site.site_title = 'Al Noir Admin'
admin.site.index_title = 'Restaurant Management'

admin.site.register(SiteSettings)
admin.site.register(Review)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject')
    ordering = ('-created_at',)