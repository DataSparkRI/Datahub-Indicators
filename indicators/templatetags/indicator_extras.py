from django import template
register = template.Library()


@register.filter(name='can_view')
def can_view(indicator, user):
    """ Check if a user can view this indicator"""
    return indicator.user_can_view(user)
