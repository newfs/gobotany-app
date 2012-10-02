from django import forms

class NewSightingForm(forms.Form):

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
    location = forms.CharField(
        max_length=120,
        widget=forms.TextInput({
            'placeholder': ('city, state OR postal code OR latitude, '
                            'longitude'),
            'pattern': (
                '(^([-\w\s]*\w)([, ]+)([-\w\s]*\w)$)|'
                '(^([a-zA-Z0-9][0-9][a-zA-Z0-9] '
                '?[0-9][a-zA-Z0-9][0-9]?)(-\d{4})?$)|'
                '(^(-?(\d{1,3}.?\d{1,6}? ?[nNsS]?))([, ]+)'
                '(-?(\d{1,3}.?\d{1,6}? ?[wWeE]?))$)'
            ),
            'required': 'required',
        })
    )
    location_notes = forms.CharField(
        required=False,
        widget=forms.Textarea({
            'placeholder': ('optional notes about plant location such as: '
                           'end of road, near oak tree'),
        })
    )
