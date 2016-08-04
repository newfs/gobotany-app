from django.shortcuts import render
from django.template import RequestContext

from gobotany.plantshare.emailconfirmation_models import EmailConfirmation


def confirm_email(request, confirmation_key):
    
    confirmation_key = confirmation_key.lower()
    email_address = EmailConfirmation.objects.confirm_email(confirmation_key)
    
    return render(request, 'emailconfirmation/confirm_email.html', {
        'email_address': email_address,
    })