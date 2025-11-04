from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('orders.urls_v1')),
]

urlpatterns += (
     # Swagger & Redoc documentation
    path('openapi.json', SpectacularAPIView.as_view(api_version='1.0', renderer_classes=[JSONRenderer]), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)