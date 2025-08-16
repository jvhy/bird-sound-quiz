from django.urls import path

from . import views

urlpatterns = [
    path("start/", views.start_view, name="start"),
    path("task/species_status/<int:region_id>", views.species_status_task_view, name="species_status")
]
