from django import forms
from autocomplete import autocomplete, AutoCompleteWidget

class ModelChoiceField(forms.ModelChoiceField):
    """
    A ModelChoiceField which uses an autocomplete widget, instead of an html
    select tag, to render its choices.
    """
    widget = AutoCompleteWidget

    def __init__(self, ac_name, reverse_label=True, view=autocomplete,
                 widget=None, **kwargs):
        self.ac_name = ac_name
        self.view = view
        if widget is None:
            widget = self.widget(ac_name, True, reverse_label, view)
        forms.Field.__init__(self, widget=widget, **kwargs)

    def _get_queryset(self):
        return self.view.settings[self.ac_name][0]
    queryset = property(_get_queryset, forms.ModelChoiceField._set_queryset)

    @property
    def to_field_name(self):
        return self.view.settings[self.ac_name][3]
