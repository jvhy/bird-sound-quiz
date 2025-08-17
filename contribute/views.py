from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import get_language

from contribute.services import get_observations_to_type_annotate
from contribute.models import ObservationTypeAnnotation
from quiz.models import Region, Observation, OccurrenceType, OCC_TYPE_DESCRIPTIONS
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
    if request.method == "POST":
        for k, v in request.POST.items():
            if k.startswith("option_"):
                annotated_occurrence_type = v
                observation_id = k.split("_")[-1]
                user = request.user
                annotation = ObservationTypeAnnotation(
                    user=user,
                    annotation=annotated_occurrence_type
                )
                annotation.observation_id = observation_id
                annotation.save()
                if user.is_superuser:
                    # Superuser annotations also go straight to main db table
                    observation = Observation.objects.get(id=observation_id)
                    observation.type = annotated_occurrence_type
                    observation.save()
        return redirect("thank_you")
    region = Region.objects.get(id=region_id)
    observations = get_observations_to_type_annotate(region=region, user=request.user)
    options = OccurrenceType.choices
    locale = get_language()
    region_name = getattr(region, f"name_{locale}") or getattr(region, f"name_en")
    return render(request, "species_status_task.html", context={"observations": observations, "options": options, "option_descriptions": OCC_TYPE_DESCRIPTIONS, "region": region_name})


@login_required
def thank_you_view(request):
    return render(request, "thank_you.html")
