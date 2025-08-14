from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("quiz/", views.quiz_page, name="quiz"),
    path("results/", views.results_page, name="results"),
    path("quiz/results/<uuid:quiz_id>/", views.results_page_get, name="results_get"),
    path("check_answer/", views.check_answer_view, name="check_answer")
]
