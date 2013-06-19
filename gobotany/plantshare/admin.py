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
    fields = ('question', 'image_link', 'asked_by', 'answer', 'category',
              'approved')
    form = QuestionAdminForm
    list_display = ('question', 'image_link', 'answer', 'asked', 'category',
                    'approved')
    ordering = ['-answered']
    readonly_fields = ['image_link', 'asked_by']
    search_fields = ['question', 'answer']

    def image_link(self, obj):
        """Present an image as a thumbnail linked to the larger version,
        for viewing when answering a question.
        """
        if obj.image:
            return '<a href="%s"><img src="%s"></a>' % (obj.image.image.url,
                                                        obj.image.thumb.url)
        else:
            return None
    image_link.short_description = 'Image'
    image_link.allow_tags = True


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
