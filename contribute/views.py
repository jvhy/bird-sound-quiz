from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import get_language

from quiz.services import get_available_regions


@login_required
def start_view(request):
    locale = get_language()
    regions = sorted(get_available_regions(locale), key=lambda r: r.display_name.lower())
    return render(request, "start.html", context={"regions": regions})
