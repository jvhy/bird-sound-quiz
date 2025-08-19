from typing import Any

from django import template


register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


@register.simple_tag
def get_localized_value(obj: Any, field: str, locale: str, fallback_locale: str = "en") -> Any:
    """
    Return the value of a localized field (e.g., field_locale) from an object.

    Args:
        obj: Object containing localized attributes.
        field: Base field name.
        locale: Locale code (e.g., "en", "fr").
        fallback_locale: Locale code to fallback on if selected locale is empty.

    Returns:
        The localized field value.
    """
    return getattr(obj, f"{field}_{locale}") or getattr(obj, f"{field}_{fallback_locale}")
