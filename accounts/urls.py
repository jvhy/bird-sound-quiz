from django.contrib.auth import views as auth_views
from django.urls import path, include

from . import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("captcha/", include("captcha.urls")),
    path("change_password/", auth_views.PasswordChangeView.as_view(template_name="change_password.html"), name="password_change"),
    path("password_change_done/", auth_views.PasswordChangeDoneView.as_view(template_name="password_change_done.html"), name="password_change_done"),
]
