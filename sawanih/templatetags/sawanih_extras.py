from django import template

register = template.Library()
_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter
def pd(value):
    """Show digits as Eastern Arabic-Indic: 12 -> ۱۲"""
    return str(value).translate(_DIGITS)
