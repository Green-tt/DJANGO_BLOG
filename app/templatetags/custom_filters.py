from django import template

register = template.Library()


@register.filter
def mul(value, args):

    try:
        return value * args
    except (TypeError, ValueError):
        return ''