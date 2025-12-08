# config/urls.py - DÜZƏLDİLMİŞ
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views import View
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# ✅ JSON FORMATINDA OPENAPI
class JSONOpenAPI(View):
    def get(self, request):
        spectacular_view = SpectacularAPIView.as_view()
        response = spectacular_view(request)
        return JsonResponse(response.data)

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path('api/analitic-', include('analitic.urls')),  
    path('openapi.json', JSONOpenAPI.as_view()),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
