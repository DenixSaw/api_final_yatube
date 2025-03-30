from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from yatube_api import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        'redoc/',
        TemplateView.as_view(template_name='redoc.html'),
        name='redoc'
    ),
    path('api/v1/jwt/create/', TokenObtainPairView.as_view(),
         name='jwt-create'),
    path('api/v1/jwt/refresh/', TokenRefreshView.as_view(),
         name='jwt-refresh'),
    path('api/v1/jwt/verify/', TokenVerifyView.as_view(),
         name='jwt-verify'),
] + static(settings.MEDIA_URL,
           document_root=settings.MEDIA_ROOT)
