from django.conf import settings


def settings_context(request):
    return {
        'LOGIN_ENABLED': settings.LOGIN_ENABLED
    }
