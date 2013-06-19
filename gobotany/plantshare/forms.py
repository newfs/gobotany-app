from django import forms
from django.core.urlresolvers import reverse_lazy

from gobotany.plantshare.models import (Checklist, ChecklistEntry,
    Location, ScreenedImage, SIGHTING_DEFAULT_VISIBILITY,
    SIGHTING_VISIBILITY_CHOICES, UserProfile)

def plant_name_suggestions_url():
    return reverse_lazy('site-plant-name-suggestions') + '?q=%s'

class LocationTextInput(forms.TextInput):
    """ Renders a location field so that a previously saved location
    appears as the user input text, rather than the ForeignKey value. """
    def render(self, name, value, attrs=None):
        if value:
            location = Location.objects.get(pk=value)
            if location:
                value = location.user_input
            else:
                value = None
        return super(LocationTextInput, self).render(name, value, attrs)


class LocationField(forms.RegexField):
    VALIDATION_MESSAGE = 'city, state OR postal code OR latitude, longitude'
    VALIDATION_PATTERN = (
        '(^([-\w\s]*\w)([, ]+)([-\w\s]*\w)$)|'
        '(^([a-zA-Z0-9][0-9][a-zA-Z0-9] ?[0-9][a-zA-Z0-9][0-9]?)(-\d{4})?$)|'
        '(^(-?(\d{1,3}.?\d{1,6}? ?[nNsS]?))([, ]+)'
        '(-?(\d{1,3}.?\d{1,6}? ?[wWeE]?))$)'
    )
    widget = LocationTextInput({'class': 'location',
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


class SightingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SightingForm, self).__init__(*args, **kwargs)
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
    latitude = forms.CharField(
        required=False,
        widget=forms.TextInput()
    )
    longitude = forms.CharField(
        required=False,
        widget=forms.TextInput()
    )
    visibility = forms.ChoiceField(choices=SIGHTING_VISIBILITY_CHOICES,
                                   initial=SIGHTING_DEFAULT_VISIBILITY)


class QuestionForm(forms.Form):
    question = forms.CharField(
        required=True,
        widget=forms.Textarea()
    )


class UserProfileForm(forms.ModelForm):
    location = LocationField()

    class Meta:
        model = UserProfile
        fields = ('details_visibility', 'display_name', 'saying',
            'location_visibility', 'location',)

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['location'].required = False

    def clean_location(self):
        if not 'location' in self.cleaned_data:
            return None
        user_text = self.cleaned_data['location']
        # Look for a Location record with the user input text.
        locations = Location.objects.filter(user_input=user_text)
        if locations.count() > 0:
            # The first one is OK because any duplicates are equivalent.
            location = locations[0]
        else:
            # Create a new location record.
            location = Location(user_input=user_text)
            location.save()
        return location

    def avatar(self):
        if self.instance.pk:
            avatar_info = self.instance.private_avatar_image()
        else:
            avatar_info = UserProfile.default_avatar_image()

        return avatar_info


class ScreenedImageForm(forms.ModelForm):
    class Meta:
        model = ScreenedImage
        fields = ('image', 'image_type')

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ('name', 'comments')

    def __init__(self, *args, **kwargs):
        super(ChecklistForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget = forms.TextInput(attrs={
            'placeholder': 'Give your plant checklist a title (required)'
            })
        self.fields['comments'].widget = forms.Textarea(attrs={
            'placeholder': 'Notes about your plant checklist',
            'rows': ''
            })

class ChecklistEntryForm(forms.ModelForm):
    class Meta:
        model = ChecklistEntry
        fields = ('plant_name', 'date_found', 'location', 'date_posted',
                  'note', 'plant_photo')

    def __init__(self, *args, **kwargs):
        super(ChecklistEntryForm, self).__init__(*args, **kwargs)
        self.fields['plant_name'].widget=forms.TextInput({
            'autocomplete': 'off',
            'autofocus': 'autofocus',
            'class': 'suggest',
            'data-suggest-url': plant_name_suggestions_url(),
            'placeholder': 'Enter Plant Name',
            'required': 'required',
        })
        self.fields['date_found'].widget = forms.DateInput(attrs={
            'placeholder': 'mm/dd/yyyy',
            'class': 'date-input'
            }, format='%m/%d/%Y')
        self.fields['location'].widget = forms.TextInput(attrs={
            'placeholder': 'Enter Location'
            })
        self.fields['date_posted'].widget = forms.DateInput(attrs={
            'placeholder': 'mm/dd/yyyy',
            'class': 'date-input'
            }, format='%m/%d/%Y')
        self.fields['note'].widget = forms.Textarea(attrs={
            'placeholder': 'Write your notes here'
            })
        self.fields['plant_photo'].widget = forms.HiddenInput()
