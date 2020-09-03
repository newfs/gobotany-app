from django import forms
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm


class RegistrationFormWithHiddenField(RegistrationForm):
    # Instead of something like ReCaptcha, just include a field
    # which will be hidden on visual browsers, which is to remain
    # blank. If anything is entered in it, such as by a spambot,
    # the form submit will be rejected.
    url = forms.CharField(
        help_text=_('Please do not enter anything in this field.'),
        label=_('URL (please leave blank)'),
        required=False,
    )

    def clean_url(self):
        url = self.cleaned_data.get('url')
        if len(url) > 0:
            raise forms.ValidationError(
                _('The URL field should be blank.'),
                code='url_field_not_blank',
            )
        return url
