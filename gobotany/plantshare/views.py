from datetime import datetime
from random import randint

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.forms.models import modelformset_factory

from gobotany.plantshare.forms import NewSightingForm, UserProfileForm, ScreenedImageForm
from gobotany.plantshare.models import Location, Sighting, UserProfile, ScreenedImage

def _new_sighting_form_page(request, form):
    """Give a new-sighting form, either blank or with as-yet-invalid data."""
    photo_image_form = ScreenedImageForm(initial={
        'image_type': 'SIGHTING'
    })
    return render(request, 'new_sighting.html', {
               'form': form,
               'photo_image_form': photo_image_form,
           }, context_instance=RequestContext(request))

def _user_name(user):
    return user.get_full_name() or user.username

# Views

def plantshare_view(request):
    """View for the main PlantShare page."""
    prior_signup_detected = request.COOKIES.get('registration_complete',
                                                False)
    return render_to_response('plantshare.html', {
               'prior_signup_detected': prior_signup_detected
           }, context_instance=RequestContext(request))

def sightings_view(request):
    """View for the sightings collection, and handling new sightings."""
    if request.method == 'POST':
        # Handle posting a new sighting to the sightings collection.
        # TODO: require login for just this HTTP verb.
        form = NewSightingForm(request.POST)
        if form.is_valid():
            location = Location(user_input=form.cleaned_data['location'])
            location.save()

            identification = form.cleaned_data['identification']
            title = form.cleaned_data['title']
            notes = form.cleaned_data['notes']
            location_notes = form.cleaned_data['location_notes']
            sighting = Sighting(user=request.user,
                                identification=identification, title=title,
                                notes=notes, location=location,
                                location_notes=location_notes)
            sighting.save()
            #print 'saved:', sighting

            done_url = reverse('ps-new-sighting-done') + '?s=%d' % sighting.id
            return HttpResponseRedirect(done_url)
        else:
            # Present the new-sighting form again for input correction.
            return _new_sighting_form_page(request, form)
    elif request.method == 'GET':
        # Return a representation of the collection of sightings.
        sightings = []
        for sighting in Sighting.objects.all()[:10]:
            sightings.append({
                'id': sighting.id,
                'identification': sighting.identification,
                'location': sighting.location,
                'user': _user_name(sighting.user),
                'created': sighting.created.strftime("%A, %B %e"),
            })

        return render_to_response('sightings.html', {
                'sightings': sightings,
               }, context_instance=RequestContext(request))
    else:
        # For an unsupported HTTP method, return a Bad Request response.
        return HttpResponse(status=400)

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
        'created': s.created
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
    ScreeningFormSet = modelformset_factory(ScreenedImage, extra=0, 
            fields=('is_approved',))
    if request.method == 'POST':
        formset = ScreeningFormSet(request.POST)
        screened_images = formset.save(commit=False)
        for image in screened_images:
            image.screened = datetime.now()
            image.screened_by = request.user
            if image.image_type == 'AVATAR' and image.is_approved:
                profile = UserProfile.objects.get(user=image.uploaded_by)
                profile.avatar = image
                profile.save()

        formset.save()

    unscreened_images = ScreenedImage.objects.filter(screened=None)
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

    if request.method == 'POST':
        form = ScreenedImageForm(request.POST, request.FILES)
        if form.is_valid():
            new_image = form.save(commit=False)
            new_image.uploaded_by = request.user
            new_image.save()

    return HttpResponse(simplejson.dumps({'success': True}), mimetype='application/json')

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
        # For now, assign one random dummy photo per sighting.
        if DUMMY_PHOTOS.has_key(plant_name):
            num_photos = len(DUMMY_PHOTOS[plant_name])
            photo_index = randint(0, num_photos - 1)
            photos.append(
                'http://newfs.s3.amazonaws.com/taxon-images-160x149/%s' % \
                    DUMMY_PHOTOS[plant_name][photo_index])

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
