from django import template
from django.core.exceptions import ObjectDoesNotExist

from gobotany.plantshare import models

register = template.Library()

def _get_user_profile(user):
    user_profile = None
    try:
        user_profile = models.UserProfile.objects.get(user=user)
    except ObjectDoesNotExist:
        pass
    return user_profile

@register.simple_tag()
def user_display_name(user):
    name = user.username
    user_profile = _get_user_profile(user)
    if user_profile:
        name = user_profile.user_display_name()
    return name

@register.simple_tag()
def unique_user_display_name(user):
    name = user.username
    user_profile = _get_user_profile(user)
    if user_profile:
        name = user_profile.unique_user_display_name()
    return name

@register.simple_tag()
def user_first_name(user):
    name = user.username
    user_profile = _get_user_profile(user)
    if user_profile:
        name = user_profile.user_first_name()
    return name

@register.assignment_tag(takes_context=True)
def assign_user_display_name(context, user):
    return user_display_name(user)

