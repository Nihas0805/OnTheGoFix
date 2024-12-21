from django import template

register = template.Library()

@register.filter
def range_filter(value):
    """Converts the value to an integer and returns a range."""
    try:
        value = int(value)  # Convert to integer
    except (ValueError, TypeError):
        return range(0)  # Default to an empty range if conversion fails
    return range(value)
