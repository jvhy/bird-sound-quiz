from typing import Any

from django import template


register = template.Library()

@register.filter
def dict_get(dictionary: dict, key: Any):
    return dictionary[key]
