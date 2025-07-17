from django.http import HttpResponse


def index(request):
    return HttpResponse("Welcome to Bird Quiz!")


def quiz_page(request):
    return HttpResponse("This page will contain the quiz slides.")


def results_page(request):
    return HttpResponse("This page will contain the quiz results.")
