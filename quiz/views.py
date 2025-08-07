import random

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from quiz.models import Recording, Quiz, Answer
from quiz.services import get_available_regions, get_species_by_region, get_quiz_recordings, get_multiple_choices


def index(request):
    regions = sorted(get_available_regions(), key=lambda r: r.display_name.lower())
    return render(request, 'index.html', context={"regions": regions})


@require_http_methods(["POST"])
def quiz_page(request):
    region_id = request.POST.get("region")
    mode = request.POST.get("mode")
    started_at = timezone.now().astimezone(timezone.get_default_timezone()).isoformat()
    region_species = get_species_by_region(region_id)
    quiz_species = random.sample(list(region_species), 10)
    recordings = get_quiz_recordings(quiz_species)
    options = {}
    match mode:
        case "MULTI":
            for sp in quiz_species:
                sp_options = get_multiple_choices(sp, region_species, 3, "random")
                options[sp.id] = sp_options
        case "OPEN":
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
            "mode": mode,
            "region_id": region_id,
            "started_at": started_at
        }
    )


@require_http_methods(["POST"])
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
    quiz = Quiz(
        user=request.user,
        mode=request.POST.get("mode"),
        started_at=request.POST.get("started_at")
    )
    quiz.region_id = request.POST.get("region_id")
    quiz.save()

    recording_ids = request.POST.getlist("ids[]")
    user_answers = []
    for i in range(10):
        user_answer = request.POST.get(f"answer_{i}")
        answer = Answer(
            quiz=quiz,
            user_answer=user_answer or ""
        )
        answer.recording_id = recording_ids[i]
        user_answers.append(answer)
    Answer.objects.bulk_create(user_answers)

    return redirect("results_get", quiz_id=quiz.id)


@require_http_methods(["GET"])
def results_page_get(request, quiz_id):
    quiz = Quiz.objects.select_related("user").get(id=quiz_id)
    answers = Answer.objects.filter(quiz=quiz).order_by("id").select_related("recording__species")
    results = [
        (
            ans.user_answer.capitalize() or "<no answer>",
            ans.recording.species.name_en.capitalize(),
            ans.recording.audio.url if settings.SELF_HOST_AUDIO else ans.recording.xc_audio_url
        )
        for ans in answers
    ]

    return render(request, "results.html", context={"score": quiz.score, "results": results})
