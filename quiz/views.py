from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return render(request, 'index.html')


def quiz_page(request):
    return HttpResponse("This page will contain the quiz slides.")


def results_page(request):
    return HttpResponse("This page will contain the quiz results.")
