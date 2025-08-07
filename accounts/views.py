from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from accounts.forms import CustomUserCreationForm


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', context={'form': form})


@login_required
def user_stats(request):
    user_quizzes = request.user.quiz_set.all()
    total_quizzes = user_quizzes.count()
    if not user_quizzes:
        accuracy = 0
        best_score = "N/A"
    else:
        accuracy = round(sum(quiz.score / quiz.length for quiz in user_quizzes) / total_quizzes * 100, 1)
        best_quiz = max(user_quizzes, key=lambda quiz: (quiz.score / quiz.length))
        best_score = f"{best_quiz.score} / {best_quiz.length}"
    return render(
        request,
        "my_stats.html",
        context = {
            "total_quizzes": total_quizzes,
            "accuracy": accuracy,
            "best_score": best_score
        }
    )
