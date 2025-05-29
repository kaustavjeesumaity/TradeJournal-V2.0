from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def endswith(value, suffix):
    """Return True if value ends with the given suffix (case-insensitive)."""
    if not isinstance(value, str):
        return False
    return value.lower().endswith(suffix.lower())
