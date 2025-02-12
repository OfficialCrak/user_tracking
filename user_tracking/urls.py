"""
URL configuration for user_tracking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, re_path, include
from user_tracking import settings
from django.conf.urls.static import static
from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


class CustomSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ['https', 'http']
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title="API Docs",
        default_version='v1',
        description="API for user_tracking",
        terms_of_service="terms_of_service/",
        contact=openapi.Contact(email="exampe@asd.com"),
        license=openapi.License(name="Архитектор Чирьев Е.А."),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    generator_class=CustomSchemaGenerator,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    re_path(r'^tracking/', include('tracking.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
