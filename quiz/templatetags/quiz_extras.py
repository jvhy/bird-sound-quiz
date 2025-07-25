from operator import attrgetter

from django import template

from quiz.models import Recording


register = template.Library()

@register.filter
def get_attr(recording: Recording, attr: str):
    """
    Gets (nested) attribute of a recording object.

    :param recording: Recording object to get an attribute from.
    :param attr: Attribute to get from Recording object, eg. "xc_audio_url" or "audio.url"
    """
    return attrgetter(attr)(recording)
