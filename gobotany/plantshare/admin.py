from django import forms
from django.contrib import admin
from gobotany.plantshare import models


class QuestionAdminForm(forms.ModelForm):
    question = forms.CharField(
        widget=forms.Textarea(attrs={'rows':3, 'cols':80})
    )
    answer = forms.CharField(
        widget=forms.Textarea(attrs={'rows':7, 'cols':80})
    )
    class Meta:
        model = models.Question


class QuestionAdmin(admin.ModelAdmin):
    date_hierarchy = 'asked'
    fields = ('question', 'asked_by', 'answer', 'category', 'approved')
    form = QuestionAdminForm
    list_display = ('question', 'answer', 'asked', 'category', 'approved')
    ordering = ['-answered']
    readonly_fields = ['asked_by']
    search_fields = ['question', 'answer']


class SightingPhotoInline(admin.StackedInline):
    model = models.Sighting.photos.through
    extra = 0


class SightingAdmin(admin.ModelAdmin):
    inlines = [SightingPhotoInline]
    exclude = ['photos']


class ScreenedImageAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Sighting, SightingAdmin)
admin.site.register(models.ScreenedImage, ScreenedImageAdmin)
