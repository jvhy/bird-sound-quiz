from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import get_language

from contribute.services import get_observations_to_type_annotate
from quiz.models import Region, Observation
from quiz.services import get_available_regions


@login_required
def start_view(request):
    if request.method == "POST":
        task = request.POST.get("task")
        match task:
            case "speciesStatusTask":
                region_id = request.POST.get("species-status-task-region")
                return redirect("species_status", region_id=region_id)
            case _:
                raise ValueError("Unknown task")
    locale = get_language()
    regions = sorted(get_available_regions(locale), key=lambda r: r.display_name.lower())
    return render(request, "start.html", context={"regions": regions})


@login_required
def species_status_task_view(request, region_id):
    region = Region.objects.get(id=region_id)
    observations = get_observations_to_type_annotate(region=region)
    options = Observation.OccurrenceType.choices
    locale = get_language()
    region_name = getattr(region, f"name_{locale}") or getattr(region, f"name_en")
    return render(request, "species_status_task.html", context={"observations": observations, "options": options, "region": region_name})
