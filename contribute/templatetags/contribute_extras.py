from typing import Any

from django import template


register = template.Library()


@register.simple_tag
def get_localized_value(obj: Any, field: str, locale: str) -> Any:
    """
    Return the value of a localized field (e.g., field_locale) from an object.

    Args:
        obj: Object containing localized attributes.
        field: Base field name.
        locale: Locale code (e.g., "en", "fr").

    Returns:
        The localized field value.
    """
    return getattr(obj, f"{field}_{locale}")
