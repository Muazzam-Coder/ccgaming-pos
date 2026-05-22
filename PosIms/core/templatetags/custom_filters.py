from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply a value by the given argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def currency(value):
    """Format a numeric value as PKR currency with two decimals."""
    try:
        val = float(value)
    except (TypeError, ValueError):
        return ''
    # Use absolute formatting for value; keep sign if negative
    sign = '-' if val < 0 else ''
    return f"{sign}PKR {abs(val):,.2f}"
