from django import db, forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from gobotany.admin import GoBotanyModelAdmin
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
        exclude = {}


class QuestionAdmin(GoBotanyModelAdmin):
    date_hierarchy = 'asked'
    fields = ('question', 'image_links', 'asked_by', 'answer', 'approved')
    form = QuestionAdminForm
    list_display = ('question', 'answer', 'asked_by', 'asked_date',
        'approved')
    list_filter = ('approved', 'answered', 'asked')
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
            return mark_safe(html)
        else:
            return None
    image_links.short_description = 'Images'


class LocationAdmin(GoBotanyModelAdmin):
    pass


class SightingAdmin(GoBotanyModelAdmin):
    fields = ('user', 'created', 'identification', 'notes', 'location_link',
        'location_notes', 'photographs', 'visibility', 'flagged',
        'approved', 'email')
    readonly_fields = ('user', 'location_link', 'photographs', 'email',)
    formfield_overrides = {
        db.models.TextField:
            {'widget': forms.Textarea(attrs={'rows': 3, 'cols': 80})},
    }
    list_display = ('identification', 'location', 'display_name', 'pics',
        'email', 'created', 'visibility', 'flagged', 'approved')
    list_filter = ('created', 'visibility', 'flagged', 'approved')
    search_fields = ('identification', 'location__city', 'location__state',)

    def location_link(self, obj):
        change_url = reverse('admin:plantshare_location_change',
            args=(obj.location.id,))
        return mark_safe('<a href="%s">%s</a>' % (change_url,
            obj.location.user_input))
    location_link.short_description = 'Location'

    def display_name(self, obj):
        display_name = ''
        try:
            profile = models.UserProfile.objects.get(user=obj.user)
            display_name = profile.user_display_name()
        except models.UserProfile.DoesNotExist:
            display_name = obj.user.username
        return display_name
    display_name.short_description = 'User'

    def email(self, obj):
        email_address = obj.user.email or ''
        return email_address

    def pics(self, obj):
        return len(obj.private_photos())

    def photographs(self, obj):
        html = ''
        for photo in obj.private_photos():
            html += '<a href="%s"><img src="%s"></a> ' % (photo.image.url,
                photo.thumb.url)
        return mark_safe(html)
    photographs.short_description = 'Photos'

class ScreenedImageAdmin(GoBotanyModelAdmin):
    list_display = ('image_type', 'uploaded', 'uploaded_by',
        'email', 'screened', 'screened_by', 'is_approved', 'admin_thumb')
    list_filter = ('is_approved',)
    list_editable = ('is_approved',)

    def email(self, obj):
        return obj.uploaded_by.email

    def admin_thumb(self, obj):
        """Show thumbnails. Doing this, because ImageKit's AdminThumbnail
        would not render."""
        try:
            html = '<img src="%s">' % obj.thumb.url
        except (FileNotFoundError, OSError) as e:
            # Return a non-existent image path so it shows up as a broken
            # image icon in the browser rather than empty space.
            html = '<img src="./error.jpg" ' + \
                'title="error retrieving image: %s">' % e
        return mark_safe(html)
    admin_thumb.short_description = 'Thumbnail'


admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Location, LocationAdmin)
admin.site.register(models.Sighting, SightingAdmin)
admin.site.register(models.ScreenedImage, ScreenedImageAdmin)
