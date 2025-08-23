import random

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from quiz.models import Recording, Quiz, Answer
from quiz.services import get_available_regions, get_regions_with_beginner_quiz, get_species_by_region, get_beginner_species_by_region, get_quiz_recordings, get_multiple_choices
from quiz.utils import check_answer


def index(request):
    regions = sorted(get_available_regions(), key=lambda r: r.display_name.lower())
    regions_with_beginner_quiz = get_regions_with_beginner_quiz()
    return render(request, 'index.html', context={"regions": regions, "beginner_quiz_regions": regions_with_beginner_quiz})


@require_http_methods(["POST"])
def quiz_page(request):
    region_id = request.POST.get("region")
    request.session["region_id"] = region_id
    mode = request.POST.get("mode")
    started_at = timezone.now().astimezone(timezone.get_default_timezone()).isoformat()
    difficulty = request.POST.get("difficulty")
    match difficulty:
        case "BGN":
            region_species = get_beginner_species_by_region(region_id)
            num_choices = 2
        case "NML":
            region_species = get_species_by_region(region_id)
            num_choices = 3
        case _:
            raise ValueError("Unexpected difficulty")
    quiz_species = random.sample(list(region_species), 10)
    recordings = get_quiz_recordings(quiz_species)
    options = {}
    match mode:
        case "MULTI":
            for sp in quiz_species:
                sp_options = get_multiple_choices(
                    target_species=sp,
                    available_species=region_species,
                    num_choices=num_choices,
                    mode="random"
                )
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
            "difficulty": difficulty,
            "mode": mode,
            "region_id": region_id,
            "started_at": started_at
        }
    )


@require_http_methods(["POST"])
def check_answer_view(request):
    recording_id = request.POST.get("id")
    user_answer = request.POST.get("user_answer")
    try:
        recording = Recording.objects.get(id=recording_id)
    except Recording.DoesNotExist:
        return JsonResponse({"error": "Recording not found"}, status=404)
    correct_answer = recording.species.name
    correct = check_answer(user_answer, recording.species)
    return JsonResponse({"answer": correct_answer, "correct": correct})


@require_http_methods(["POST"])
def results_page(request):
    quiz = Quiz(
        mode=request.POST.get("mode"),
        difficulty=request.POST.get("difficulty"),
        started_at=request.POST.get("started_at")
    )
    quiz.user_id = request.user.id
    quiz.region_id = request.POST.get("region_id")

    recording_ids = request.POST.getlist("ids[]")
    answer_statuses = request.POST.getlist("is_correct[]")

    user_answers = []
    score = 0
    for i, (recording_id, answer_status) in enumerate(zip(recording_ids, answer_statuses)):
        user_answer = request.POST.get(f"answer_{i}")
        recording = Recording.objects.get(id=recording_id)
        is_correct = bool(int(answer_status))
        score += is_correct
        answer = Answer(
            quiz=quiz,
            recording=recording,
            user_answer=user_answer or "",
            is_correct=is_correct
        )
        user_answers.append(answer)

    quiz.length = len(user_answers)
    quiz.score = score
    quiz.save()
    Answer.objects.bulk_create(user_answers)

    return redirect("results_get", quiz_id=quiz.id)


@require_http_methods(["GET"])
def results_page_get(request, quiz_id):
    quiz = Quiz.objects.select_related("user").get(id=quiz_id)
    answers = Answer.objects.filter(quiz=quiz).order_by("id").select_related("recording__species")
    placeholder = _("EmptyAnswerPlaceholderText")
    results = [
        (
            ans.user_answer or f"<{placeholder}>",
            ans.recording.species.name,
            ans.is_correct,
            ans.recording.audio.url if settings.SELF_HOST_AUDIO else ans.recording.xc_audio_url
        )
        for ans in answers
    ]

    return render(request, "results.html", context={"score": quiz.score, "results": results})
