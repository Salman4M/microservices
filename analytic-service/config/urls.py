from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('analitic.urls')),  

    path('openapi.json', SpectacularAPIView.as_view(api_version='1.0', renderer_classes=[JSONRenderer]), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

