"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "Educational Management Admin"
admin.site.site_title = "EMS Admin Portal"
admin.site.index_title = "Welcome to the Educational Management System"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.urls")),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/dist/img/favicon.ico", permanent=True),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler400 = "config.errors.error_400"
handler403 = "config.errors.error_403"
handler404 = "config.errors.error_404"
handler500 = "config.errors.error_500"
