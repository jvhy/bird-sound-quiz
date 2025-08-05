import random

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from quiz.models import Recording
from quiz.services import get_available_regions, get_species_by_region, get_quiz_recordings, get_multiple_choices


def index(request):
    regions = sorted(get_available_regions(), key=lambda r: r.display_name.lower())
    return render(request, 'index.html', context={"regions": regions})


@require_http_methods(["POST"])
def quiz_page(request):
    region_id = request.POST.get("region")
    mode = request.POST.get("mode")
    region_species = get_species_by_region(region_id)
    quiz_species = random.sample(list(region_species), 10)
    recordings = get_quiz_recordings(quiz_species)
    options = {}
    match mode:
        case "choice":
            for sp in quiz_species:
                sp_options = get_multiple_choices(sp, region_species, 3, "random")
                options[sp.id] = sp_options
        case "open":
            pass
        case _:
            raise ValueError("Unexpected game mode")
    audio_field = "audio.url" if settings.SELF_HOST_AUDIO else "xc_audio_url"
    return render(
        request,
        'quiz.html',
        context={
            "recordings": recordings,
            "audio_field": audio_field,
            "options": options,
            "mode": mode
        }
    )


@require_http_methods(["POST"])
@csrf_exempt  # TODO: handle CSRF token in JS
def check_answer(request):
    recording_id = request.POST.get("id")
    user_answer = request.POST.get("user_answer")
    try:
        recording = Recording.objects.get(id=recording_id)
    except Recording.DoesNotExist:
        return JsonResponse({"error": "Recording not found"}, status=404)
    correct_answer = recording.species.name_en
    correct = user_answer.strip().capitalize() == correct_answer.strip().capitalize() if user_answer else False
    return JsonResponse({"answer": correct_answer, "correct": correct})


@require_http_methods(["POST"])
def results_page(request):
    recording_ids = request.POST.getlist("ids[]")
    user_answers = []
    for i in range(10):
        answer = request.POST.get(f"answer_{i}")
        answer = answer.capitalize() if answer else "<no answer>"
        user_answers.append(answer)
    audio_urls = request.POST.getlist("audio_urls[]")
    recordings = Recording.objects.filter(id__in=recording_ids).select_related("species")
    recordings_by_id = {str(r.id): r for r in recordings}
    correct_answers = [recordings_by_id[rec_id].species.name_en.capitalize() for rec_id in recording_ids]
    results = list(zip(user_answers, correct_answers, audio_urls))
    score = sum(ua == ca for ua, ca, _ in results)
    return render(request, 'results.html', context={"score": score, "results": results})
