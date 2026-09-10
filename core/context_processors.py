from django.core.cache import cache

from .models import SITE_SETTINGS_CACHE_KEY, SiteSettings

SITE_SETTINGS_CACHE_TIMEOUT = 300
_UNSET = object()


def site_settings(request):
    settings_obj = cache.get(SITE_SETTINGS_CACHE_KEY, _UNSET)
    if settings_obj is _UNSET:
        settings_obj = SiteSettings.objects.first()
        cache.set(SITE_SETTINGS_CACHE_KEY, settings_obj, SITE_SETTINGS_CACHE_TIMEOUT)
    return {
        'site_settings': settings_obj
    }