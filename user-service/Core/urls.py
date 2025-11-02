from django.contrib import admin
from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.renderers import JSONRenderer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('user_service.urls')),
    
]

urlpatterns += (
     # Swagger & Redoc documentation
    path('openapi.json', SpectacularAPIView.as_view(api_version='1.0', renderer_classes=[JSONRenderer]), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
)