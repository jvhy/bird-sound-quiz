from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from quiz.models import Recording
from quiz.services import get_available_regions, get_species_by_region, get_quiz_recordings


def index(request):
    regions = get_available_regions()
    return render(request, 'index.html', context={"regions": regions})


@require_http_methods(["POST"])
def quiz_page(request):
    region_id = request.POST.get('region')
    quiz_species = get_species_by_region(region_id, 10)
    recordings = get_quiz_recordings(quiz_species)
    audio_field = "audio.url" if settings.SELF_HOST_AUDIO else "xc_audio_url"
    return render(request, 'quiz.html', context={"recordings": recordings, "audio_field": audio_field})


@require_http_methods(["POST"])
def results_page(request):
    recording_ids = request.POST.getlist("ids[]")
    user_answers = [ans.capitalize() if ans else "<no answer>" for ans in request.POST.getlist("answers[]")]
    audio_urls = request.POST.getlist("audio_urls[]")
    recordings = Recording.objects.filter(id__in=recording_ids).select_related("species")
    recordings_by_id = {str(r.id): r for r in recordings}
    correct_answers = [recordings_by_id[rec_id].species.name_en.capitalize() for rec_id in recording_ids]
    results = list(zip(user_answers, correct_answers, audio_urls))
    score = sum(ua == ca for ua, ca, _ in results)
    return render(request, 'results.html', context={"score": score, "results": results})
