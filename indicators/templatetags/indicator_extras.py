from django import template
register = template.Library()


@register.filter(name='can_view')
def can_view(indicator, request):
    """ Check if a user can view this indicator"""
    pk = getattr(request.user, 'pk', None)
    if pk:
        return indicator.user_can_view(pk)
    else:
        return indicator.user_can_view(user=None)
