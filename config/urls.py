from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import set_language


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('menu/', include('menu.urls')),
path('reservations/', include('reservations.urls')
),
    path('operations/', include('operations.urls')),
    path('i18n/set-language/', set_language, name='set_language'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
