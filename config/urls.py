"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from lili_api.routers import router as lili_router
from lili_api.authentication.views import LoginView, LogoutView, RefreshView, MeView, RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from lili_api.views import ContactoView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', LoginView.as_view()),
    path('api/auth/refresh/', RefreshView.as_view()),
    path('api/auth/me/', MeView.as_view()),
    path('api/auth/logout/', LogoutView.as_view()),
    path('api/auth/register/', RegisterView.as_view()),
    path('api/', include(lili_router.urls)),
    path('api/contact/', ContactoView.as_view()),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
