from django import forms
from django.contrib import admin

from gobotany.plantshare.models import Question

class QuestionAdminForm(forms.ModelForm):
    question = forms.CharField(
        widget=forms.Textarea(attrs={'rows':3, 'cols':80})
    )
    answer = forms.CharField(
        widget=forms.Textarea(attrs={'rows':7, 'cols':80})
    )
    class Meta:
        model = Question

class QuestionAdmin(admin.ModelAdmin):
    date_hierarchy = 'asked'
    fields = ('question', 'asked_by', 'answer', 'category')
    form = QuestionAdminForm
    list_display = ('question', 'answer', 'asked', 'category')
    ordering = ['-answered']
    readonly_fields = ['asked_by']
    search_fields = ['question', 'answer']

admin.site.register(Question, QuestionAdmin)
