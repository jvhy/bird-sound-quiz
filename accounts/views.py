from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from accounts.forms import CustomAuthenticationForm, CustomUserCreationForm
from quiz.services import get_available_regions


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm

    def form_valid(self, form):
        messages.success(self.request, _("LoginSuccessMessage"))
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, _("LogoutSuccessMessage"))
        return super().dispatch(request, *args, **kwargs)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _("RegistrationSuccessMessage"))
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', context={'form': form})


@require_http_methods(["POST"])
@login_required
def delete_account(request):
    user = request.user
    logout(request)
    user.delete()
    return redirect("account_deleted")


def account_deleted(request):
    return render(request, "account_deleted.html")


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


@login_required
def user_profile(request):
    if request.method == "POST":
        region_id = request.POST.get("region")
        user = request.user
        user.preferred_region_id = region_id
        user.save()
    available_regions = sorted(get_available_regions(), key=lambda r: r.display_name.lower())
    return render(request, "my_profile.html", context={"regions": available_regions})
