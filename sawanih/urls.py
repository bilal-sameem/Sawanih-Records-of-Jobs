from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", include("login.urls")),
    path("", include("sawanih.app_urls")),   # keep this last
]