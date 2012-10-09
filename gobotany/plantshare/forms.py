
from django import forms

from models import UserProfile

class LocationField(forms.RegexField):
    VALIDATION_MESSAGE = 'city, state OR postal code OR latitude, longitude'
    VALIDATION_PATTERN = (
        '(^([-\w\s]*\w)([, ]+)([-\w\s]*\w)$)|'
        '(^([a-zA-Z0-9][0-9][a-zA-Z0-9] ?[0-9][a-zA-Z0-9][0-9]?)(-\d{4})?$)|'
        '(^(-?(\d{1,3}.?\d{1,6}? ?[nNsS]?))([, ]+)'
        '(-?(\d{1,3}.?\d{1,6}? ?[wWeE]?))$)'
    )
    widget = forms.TextInput({'placeholder': VALIDATION_MESSAGE,
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

    def _location_validation_message():
        return 'city, state OR postal code OR latitude, longitude'

    def _location_validation_pattern():
        return (
                '(^([-\w\s]*\w)([, ]+)([-\w\s]*\w)$)|'
                '(^([a-zA-Z0-9][0-9][a-zA-Z0-9] '
                '?[0-9][a-zA-Z0-9][0-9]?)(-\d{4})?$)|'
                '(^(-?(\d{1,3}.?\d{1,6}? ?[nNsS]?))([, ]+)'
                '(-?(\d{1,3}.?\d{1,6}? ?[wWeE]?))$)'
        )

    identification = forms.CharField(
        max_length=120,
        widget=forms.TextInput({
            'autocomplete': 'off',
            'autofocus': 'autofocus',
            'placeholder': 'scientific or common name',
            'required': 'required',
        })
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

