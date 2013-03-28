from datetime import datetime
from random import randint

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.forms import widgets
from django.forms.models import modelformset_factory

from gobotany.plantshare.forms import (NewSightingForm, UserProfileForm,
                                       ScreenedImageForm)
from gobotany.plantshare.models import (Location, Sighting, UserProfile,
                                        ScreenedImage, Question)

SIGHTINGS_MAP_DEFAULTS = {
    'latitude': '44.53599',
    'longitude': '-70.56609',
    'center_title': 'Rumford, Maine'
}

def _new_sighting_form_page(request, form):
    """Give a new-sighting form, either blank or with as-yet-invalid data."""
    upload_photo_form = ScreenedImageForm(initial={
        'image_type': 'SIGHTING'
    })

    return render(request, 'new_sighting.html', {
               'form': form,
               'upload_photo_form': upload_photo_form,
           }, context_instance=RequestContext(request))

def _user_name(user):
    return user.get_full_name() or user.username

# Views

def _get_recently_answered_questions(number_of_questions):
    questions = Question.objects.all().exclude(
        answer__exact='').order_by(
        '-answered')[:number_of_questions]
    return questions

def plantshare_view(request):
    """View for the main PlantShare page."""

    MAX_RECENTLY_ANSWERED_QUESTIONS = 3
    questions = _get_recently_answered_questions(
                MAX_RECENTLY_ANSWERED_QUESTIONS)

    prior_signup_detected = request.COOKIES.get('registration_complete',
                                                False)

    avatar_info = UserProfile.default_avatar_image()
    if request.user.is_authenticated():
        try:
            profile = UserProfile.objects.get(user=request.user)
            avatar_info = profile.private_avatar_image()
        except UserProfile.DoesNotExist:
            avatar_info = UserProfile.default_avatar_image()

    return render_to_response('plantshare.html', {
               'prior_signup_detected': prior_signup_detected,
               'avatar': avatar_info,
               'map': SIGHTINGS_MAP_DEFAULTS,
               'questions': questions,
               'max_questions': MAX_RECENTLY_ANSWERED_QUESTIONS
           }, context_instance=RequestContext(request))

def sightings_view(request):
    """View for the sightings collection: showing a list of recent sightings
    (GET) as well as handling adding a new sighting (the POST action from
    the new-sighting form).
    """
    MAX_RECENT_SIGHTINGS = 50

    if request.method == 'POST':
        # Handle posting a new sighting to the sightings collection.
        if request.user.is_authenticated():
            form = NewSightingForm(request.POST)
            if form.is_valid():
                location = Location(user_input=form.cleaned_data['location'],
                                    latitude=form.cleaned_data['latitude'],
                                    longitude=form.cleaned_data['longitude'])
                location.save()

                identification = form.cleaned_data['identification']
                notes = form.cleaned_data['notes']
                location_notes = form.cleaned_data['location_notes']
                sighting = Sighting(user=request.user,
                                    identification=identification, title='',
                                    notes=notes, location=location,
                                    location_notes=location_notes)

                sighting.save()

                #print 'saved:', sighting
                photo_ids = request.POST.getlist('sightings_photos')
                #print 'Got sightings photos: ', sighting_photos
                photos = ScreenedImage.objects.filter(id__in=photo_ids)
                sighting.photos.add(*photos)
                sighting.save()

                done_url = (reverse('ps-new-sighting-done') + '?s=%d'
                            % sighting.id)
                return HttpResponseRedirect(done_url)
            else:
                # Present the new-sighting form again for input correction.
                return _new_sighting_form_page(request, form)
        else:
            return HttpResponse(status=401)   # 401 Unauthorized
    elif request.method == 'GET':
        # Return a representation of the collection of sightings.
        sightings_queryset = Sighting.objects.all().select_related().\
            prefetch_related('location')[:MAX_RECENT_SIGHTINGS]
        sightings = []
        for sighting in sightings_queryset:
            sightings.append({
                'id': sighting.id,
                'identification': sighting.identification,
                'location': sighting.location,
                'user': _user_name(sighting.user),
                'created': sighting.created.strftime("%A, %B %e"),
            })

        return render_to_response('sightings.html', {
                    'sightings': sightings
               }, context_instance=RequestContext(request))
    else:
        # For an unsupported HTTP method, return a Bad Request response.
        return HttpResponse(status=400)

def sightings_locator_view(request):
    return render_to_response('sightings_locator.html', {
                'map': SIGHTINGS_MAP_DEFAULTS
           }, context_instance=RequestContext(request))

def sighting_view(request, sighting_id):
    """View for an individual sighting."""
    s = Sighting.objects.get(id=sighting_id)
    sighting = {
        'id': s.id,
        'identification': s.identification,
        'notes': s.notes,
        'location': s.location,
        'location_notes': s.location_notes,
        'user': _user_name(s.user),
        'created': s.created,
        'photos': s.private_photos()
    }
    return render_to_response('sighting.html', {
               'sighting': sighting,
           }, context_instance=RequestContext(request))

@login_required
def new_sighting_view(request):
    """View for a blank form for posting a new sighting."""
    form = NewSightingForm()
    return _new_sighting_form_page(request, form)

@login_required
def new_sighting_done_view(request):
    """View for a confirmation page upon posting a new sighting."""
    return render_to_response('new_sighting_done.html', {
           }, context_instance=RequestContext(request))

def questions_view(request):
    """View for the main Ask the Botanist page and the questions collection:
    showing a list of recent questions (GET) as well as handling adding a new
    question (the POST action from the question form).
    """
    MAX_RECENTLY_ANSWERED_QUESTIONS = 10

    if request.method == 'POST':
        # Handle posting a new question to the questions collection.
        if request.user.is_authenticated():
            question_text = request.POST['question']
            question = Question(question=question_text, asked_by=request.user)
            question.save()

            done_url = reverse('ps-new-question-done')
            return HttpResponseRedirect(done_url)
        else:
            return HttpResponse(status=401)   # 401 Unauthorized
    elif request.method == 'GET':
        questions = _get_recently_answered_questions(
                    MAX_RECENTLY_ANSWERED_QUESTIONS)
        return render_to_response('ask.html', {
                    'questions': questions
            }, context_instance=RequestContext(request))
    else:
        # For an unsupported HTTP method, return a Bad Request response.
        return HttpResponse(status=400)

def all_questions_view(request):
    """View for the full list of Questions and Answers."""
    questions = Question.objects.all().exclude(
        answer__exact='').order_by(
        'category', '-answered')
    return render_to_response('all_questions.html', {
            'questions': questions
        }, context_instance=RequestContext(request))


@login_required
def new_question_done_view(request):
    """View for a confirmation page upon asking a new question."""
    return render_to_response('new_question_done.html', {
           }, context_instance=RequestContext(request))

@login_required
def profile_view(request):
    """View for the logged-in user's profile."""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None

    profile_form = UserProfileForm(instance=profile)
    avatar_form = ScreenedImageForm(initial={
        'image_type': 'AVATAR'
    })

    context = {
        'profile_form': profile_form,
        'avatar_form': avatar_form,
    }
    return render_to_response('profile.html', context,
            context_instance=RequestContext(request))

@login_required
@user_passes_test(lambda u: u.is_staff, login_url=reverse_lazy('ps-main'))
def screen_images(request):

    # Use RadioSelect widget for approval field
    def override_is_approved(field):
        if field.name == 'is_approved':
            return field.formfield(widget=widgets.RadioSelect(choices=[
                (True, 'Yes'), 
                (False, 'No')]))

    ScreeningFormSet = modelformset_factory(ScreenedImage, extra=0, 
            fields=('is_approved',), formfield_callback=override_is_approved)

    if request.method == 'POST':
        formset = ScreeningFormSet(request.POST)
        for form in formset.initial_forms:
            form.instance.screened = datetime.now()
            form.instance.screened_by = request.user
            # Forms left as "unapproved" appear unchanged, so they won't be
            # saved with formset.save()
            form.instance.save()

        approved_images = formset.save()
        for image in approved_images:
            if image.image_type == 'AVATAR' and image.is_approved:
                profile = UserProfile.objects.get(user=image.uploaded_by)
                if profile.avatar:
                    # Orphan the user's previous avatars for later deletion
                    old_avatar = profile.avatar
                    old_avatar.orphaned = True
                    old_avatar.save()
                profile.avatar = image
                profile.save()

    unscreened_images = ScreenedImage.objects.filter(screened=None,
            deleted=False, orphaned=False)
    formset = ScreeningFormSet(queryset=unscreened_images)

    context = {
        'screening_formset': formset,
    }
    return render_to_response('staff/screen_images.html', context,
            context_instance=RequestContext(request))


# AJAX API
def ajax_profile_edit(request):
    """ Ajax form submission of profile form """
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps({
            'error': True,
            'info': 'User is not authenticated.'
        }), mimetype='application/json')

    if request.method == 'POST':
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        if profile_form.is_valid():
            profile = profile_form.save(commit=False)
            if not profile.user:
                profile.user = request.user
            profile.save()
            profile_form.save_m2m()
        else:
            return HttpResponse(simplejson.dumps({
                'error': True,
                'info': 'Form Validation error:\n{0}'.format(profile_form.errors.as_text())
            }), mimetype='application/json')

    return HttpResponse(simplejson.dumps({'success': True}), mimetype='application/json')

def ajax_image_upload(request):
    """ Ajax form submission of image upload form """
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps({
            'error': True,
            'info': 'Authentication error'
        }), mimetype='application/json')

    response = {
        'success': True
    }
    if request.method == 'POST':
        form = ScreenedImageForm(request.POST, request.FILES)
        if form.is_valid():
            new_image = form.save(commit=False)
            new_image.uploaded_by = request.user
            new_image.save()

            if new_image.image_type == 'AVATAR':
                # Since we're technically editing the user's profile by 
                # uploading an avatar, create a user profile if they don't
                # have one. Otherwise, this avatar image ends up in limbo.
                profile, created = None, False
                try:
                    profile = UserProfile.objects.get(user=request.user)
                except UserProfile.DoesNotExist:
                    profile = UserProfile()
                    profile.display_name = request.user.username

                if not created:
                    # Flag all previous, unscreened avatars as "orphaned,"
                    # since the user has essentially changed his mind and
                    # uploaded this new image.
                    previous_avatars = ScreenedImage.objects.filter(
                            image_type='AVATAR',
                            uploaded_by=request.user,
                            screened__isnull=True,
                            deleted=False,
                            orphaned=False,
                            uploaded__lt=new_image.uploaded
                    )
                    previous_avatars.update(orphaned=True)

            response.update({
                'id': new_image.pk,
                'thumb': new_image.thumb.url,
                'url': new_image.image.url,
            })


    return HttpResponse(simplejson.dumps(response), mimetype='application/json')

def ajax_image_reject(request, image_id):
    """ Reject an image that was previously uploaded. """
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps({
            'error': True,
            'info': 'Authentication error'
        }), mimetype='application/json')

    image = ScreenedImage.objects.get(pk=image_id)

    # Only staff or the user who originally uploaded the image may reject it.
    if not (request.user.is_staff or request.user == image.uploaded_by):
        return HttpResponse(simplejson.dumps({
            'error': True,
            'info': 'Authentication error'
        }), mimetype='application/json')

    image.is_approved = False
    image.screened = datetime.now()
    image.screened_by = request.user

    image.save()

    response = {
        'success': True
    }

    return HttpResponse(simplejson.dumps(response), mimetype='application/json')

def ajax_sightings(request):
    """Return sightings data for a plant."""

    MAX_TO_RETURN = 100

    # TODO: replace dummy photos with actual ones
    DUMMY_PHOTOS = {
        'Acer saccharum': [
            'Sapindaceae/acer-saccharum-ha-atal-a.jpg',
            'Sapindaceae/acer-saccharum-ba-atal.jpg',
            'Sapindaceae/acer-saccharum-fl-ahaines-a.jpg',
            'Sapindaceae/acer-saccharum-fl-ahaines-b.jpg',
            'Sapindaceae/acer-saccharum-fl-apratt.jpg',
            'Sapindaceae/acer-saccharum-fl-dcameron-a.jpg',
            'Sapindaceae/acer-saccharum-fl-dcameron-b.jpg',
            'Sapindaceae/acer-saccharum-fr-sbaskauf.jpg',
            'Sapindaceae/acer-saccharum-ha-fbramley-a.jpg',
            'Sapindaceae/acer-saccharum-ha-fbramley-c.jpg',
            'Sapindaceae/acer-saccharum-le-ahaines.jpg'
        ],
        'Nymphaea odorata': [
            'Nymphaeaceae/nymphaea-odorata-ff-dkausen.jpg',
            'Nymphaeaceae/nymphaea-odorata-ff-dcameron-b.jpg',
            'Nymphaeaceae/nymphaea-odorata-ff-ahaines.jpg',
            'Nymphaeaceae/nymphaea-odorata-ff-ddentzer.jpg',
            'Nymphaeaceae/nymphaea-odorata-ha-dcameron-a.jpg',
            'Nymphaeaceae/nymphaea-odorata-in-cevans.jpg',
            'Nymphaeaceae/nymphaea-odorata-le-lnewcomb.jpg',
            'Nymphaeaceae/nymphaea-odorata-sf-glienau.jpg',
            'Nymphaeaceae/nymphaea-odorata-st-dcameron-c.jpg'
        ],
    }

    plant_name = request.GET.get('plant')

    sightings = Sighting.objects.select_related('location', 'user').filter(
                    identification__iexact=plant_name)[:MAX_TO_RETURN]
    sightings_json = []
    for sighting in sightings:
        name = _user_name(sighting.user)

        photos = []
        for photo in sighting.approved_photos():
            photos.append(photo.thumb.url)

        # TODO: temporary, remove before release:
        # If there are no approved photos yet for this sighting, look
        # through the test images and if such exist, assign one random
        # dummy photo per sighting. This is just to keep the test data
        # working a little while longer.
        if len(photos) == 0 and DUMMY_PHOTOS.has_key(plant_name):
                num_photos = len(DUMMY_PHOTOS[plant_name])
                photo_index = randint(0, num_photos - 1)
                photos.append(
                    'http://%s.s3.amazonaws.com/taxon-images-160x149/%s' \
                        % (
                    getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'newfs'),
                    DUMMY_PHOTOS[plant_name][photo_index]))

        sightings_json.append({
            'id': sighting.id,
            'created': unicode(sighting.created.strftime("%A, %B %e, %Y")),
            'location': sighting.location.user_input,
            'latitude': sighting.location.latitude,
            'longitude': sighting.location.longitude,
            'user': name,
            'description': sighting.notes,
            'photos': photos,
        })

    json = {
        'scientific_name': plant_name,
        'sightings': sightings_json
    }

    return HttpResponse(simplejson.dumps(json),
                        mimetype='application/json; charset=utf-8')
