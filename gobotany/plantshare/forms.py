
from django import forms
from django.core.urlresolvers import reverse_lazy

from models import UserProfile

def plant_name_suggestions_url():
    return reverse_lazy('site-plant-name-suggestions') + '?q=%s'

class LocationField(forms.RegexField):
    VALIDATION_MESSAGE = 'city, state OR postal code OR latitude, longitude'
    VALIDATION_PATTERN = (
        '(^([-\w\s]*\w)([, ]+)([-\w\s]*\w)$)|'
        '(^([a-zA-Z0-9][0-9][a-zA-Z0-9] ?[0-9][a-zA-Z0-9][0-9]?)(-\d{4})?$)|'
        '(^(-?(\d{1,3}.?\d{1,6}? ?[nNsS]?))([, ]+)'
        '(-?(\d{1,3}.?\d{1,6}? ?[wWeE]?))$)'
    )
    widget = forms.TextInput({'class': 'location',
                              'placeholder': VALIDATION_MESSAGE,
                              'pattern': VALIDATION_PATTERN})
    default_error_messages = {
        'invalid': 'Enter %s.' % VALIDATION_MESSAGE
    }

    def __init__(self, required=True, max_length=120, min_length=None, *args,
                 **kwargs):
        super(LocationField, self).__init__(required, max_length, min_length,
                                            *args, **kwargs)
        self._set_regex(LocationField.VALIDATION_PATTERN)
        if required:
            self.widget.attrs['required'] = 'required'


class NewSightingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(NewSightingForm, self).__init__(*args, **kwargs)
        # Set up a widget here instead of in its regular declaration in
        # order to work around an error regarding a 'reverse' URL.
        self.fields['identification'].widget=forms.TextInput({
            'autocomplete': 'off',
            'autofocus': 'autofocus',
            'class': 'suggest',
            'data-suggest-url': plant_name_suggestions_url(),
            'placeholder': 'scientific or common name',
            'required': 'required',
        })

    identification = forms.CharField(
        max_length=120,
        # Set up the widget in __init__, so we can get the correct AJAX URL
        # for plant name suggestions by use of 'reverse'. Without using
        # __init__, an error occurs. Using reverse_lazy alone does not work.
        # http://stackoverflow.com/questions/7430502/
    )
    title = forms.CharField(
        max_length=120,
        widget=forms.TextInput({
            'required': 'required',
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(),
    )
    location = LocationField()
    location_notes = forms.CharField(
        required=False,
        widget=forms.Textarea({
            'placeholder': ('optional notes about plant location such as: '
                           'end of road, near oak tree'),
        })
    )


class UserProfileForm(forms.ModelForm): 
    class Meta:
        model = UserProfile
        fields = ('sharing_visibility', 'display_name', 'saying',)

