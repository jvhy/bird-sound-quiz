from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("quiz/", views.quiz_page, name="quiz"),
    path("results/", views.results_page, name="results"),
    path("check_answer/", views.check_answer, name="check_answer")
]
