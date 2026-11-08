from django.urls import path
from . import views

app_name = "sawanih"
urlpatterns = [
    # pages (GET)
    path("", views.dashboard, name="dashboard"),
    path("persons/new/", views.person_new, name="person_new"),
    path("persons/<int:pk>/", views.person_detail, name="person_detail"),
    path("persons/<int:pk>/edit/", views.person_edit, name="person_edit"),
    path("reports/", views.reports, name="reports"),
    path("reports/export/", views.reports_export, name="reports_export"),
    # API
    path("api/persons/", views.api_person_create, name="api_person_create"),          # POST
    path("api/persons/<int:pk>/", views.api_person_item, name="api_person_item"),     # PUT, DELETE
]
