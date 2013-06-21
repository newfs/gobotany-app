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
    fields = ('question', 'image_links', 'asked_by', 'answer', 'category',
              'approved')
    form = QuestionAdminForm
    list_display = ('question', 'answer', 'asked', 'category', 'approved')
    list_filter = ('category', 'approved', 'answered', 'asked')
    ordering = ['-answered']
    readonly_fields = ['image_links', 'asked_by']
    search_fields = ['question', 'answer']

    def image_links(self, obj):
        """Present images as thumbnails linked to the larger versions,
        for viewing when answering a question.
        """
        html = ''
        images = obj.images.all()
        if images:
            for image in images:
                html += '<a href="%s"><img src="%s"></a> ' % (
                    image.image.url, image.thumb.url)
            return html
        else:
            return None
    image_links.short_description = 'Images'
    image_links.allow_tags = True


class SightingPhotoInline(admin.StackedInline):
    model = models.Sighting.photos.through
    extra = 0


class SightingAdmin(admin.ModelAdmin):
    inlines = [SightingPhotoInline]
    exclude = ['photos']
    list_display = ('display_name', 'identification', 'created', 'location',)
    search_fields = ('identification', 'location__city', 'location__state',)

    def display_name(self, obj):
        display_name = ''
        try: 
            profile = models.UserProfile.objects.get(user=obj.user)
            display_name = profile.user_display_name()
        except models.UserProfile.DoesNotExist:
            display_name = obj.user.username

        return display_name




class ScreenedImageAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Sighting, SightingAdmin)
admin.site.register(models.ScreenedImage, ScreenedImageAdmin)
