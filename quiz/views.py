from django.shortcuts import render

from quiz.models import Recording
from quiz.services import get_quiz_recordings


def index(request):
    return render(request, 'index.html')


def quiz_page(request):
    recordings = get_quiz_recordings(10)
    return render(request, 'quiz.html', context={"recordings": recordings})


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
