# user-service/Core/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.renderers import JSONRenderer

urlpatterns = [
    path('user-admin/', admin.site.urls),
    path('api/', include('user_service.urls')),  # Add api/ prefix here since user_service urls don't have it
]

urlpatterns += (
    path('openapi.json', SpectacularAPIView.as_view(api_version='1.0', renderer_classes=[JSONRenderer]), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
)


