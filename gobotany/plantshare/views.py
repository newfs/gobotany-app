import csv

from datetime import datetime
from random import randint

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.forms import widgets
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import (get_object_or_404, redirect, render,
    render_to_response)
from django.template import RequestContext
from django.utils import simplejson

from gobotany.plantshare.forms import (ChecklistEntryForm, ChecklistForm,
    QuestionForm, ScreenedImageForm, SightingForm, UserProfileForm)
from gobotany.plantshare.models import (Checklist, ChecklistCollaborator,
    ChecklistEntry, Location, Question, ScreenedImage, Sighting,
    SIGHTING_VISIBILITY_CHOICES, UserProfile)
from gobotany.plantshare.utils import restrictions

SIGHTINGS_MAP_DEFAULTS = {
    'latitude': '43.66',
    'longitude': '-70.27',
    'center_title': 'Portland, Maine',
    'zoom': '7'
}

SIGHTING_DATE_FORMAT = "%e %B %Y"
SIGHTING_DAY_DATE_FORMAT = '%A, ' + SIGHTING_DATE_FORMAT
SIGHTING_DATE_TIME_FORMAT = SIGHTING_DAY_DATE_FORMAT + " at %I:%M %p"

def _sighting_form_page(request, form, edit=False, sighting=None):
    """Return a sighting form, either blank or with data."""
    template = 'new_sighting.html'
    if edit == True:
        template = 'edit_sighting.html'

    upload_photo_form = ScreenedImageForm(initial={
        'image_type': 'SIGHTING'
    })
    created = None
    if sighting:
        created = sighting.created.strftime(SIGHTING_DAY_DATE_FORMAT)
        upload_photo_form = ScreenedImageForm(initial={
            'image_type': 'SIGHTING'
        })

    return render(request, template, {
               'form': form,
               'upload_photo_form': upload_photo_form,
               'sighting': sighting,
               'created': created,
           }, context_instance=RequestContext(request))


def _create_checklistentry_formset(**kwargs):
    return modelformset_factory(ChecklistEntry, form=ChecklistEntryForm,
            extra=1, **kwargs)


# Views

def _get_recently_answered_questions(number_of_questions):
    questions = Question.objects.answered().order_by(
        '-answered')[:number_of_questions]
    return questions


def plantshare_view(request):
    """View for the main PlantShare page."""
    upload_photo_form = ScreenedImageForm(initial={
        'image_type': 'QUESTION'
    })
    MAX_RECENTLY_ANSWERED_QUESTIONS = 3
    questions = _get_recently_answered_questions(
                MAX_RECENTLY_ANSWERED_QUESTIONS)
    max_question_length = Question._meta.get_field('question').max_length

    prior_signup_detected = request.COOKIES.get('registration_complete',
                                                False)

    avatar_info = UserProfile.default_avatar_image()
    profile = None
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
                'max_questions': MAX_RECENTLY_ANSWERED_QUESTIONS,
                'max_question_length': max_question_length,
                'upload_photo_form': upload_photo_form,
                'profile': profile
           }, context_instance=RequestContext(request))

def _may_show_sighting(sighting, user):
    """Determine whether a sighting may be shown to a user in a set of
    results (list, table, map markers, etc.).
    """
    may_show_sighting = False

    if sighting.visibility == 'PUBLIC':
        may_show_sighting = True
    if (sighting.visibility == 'USERS') and user.is_authenticated():
        may_show_sighting = True
    #elif:
        # TODO: later when available, handle GROUPS visibility
    elif sighting.visibility == 'PRIVATE':
        if (((user.id == sighting.user.id) or user.is_staff) and
                user.is_authenticated()):
            may_show_sighting = True

    return may_show_sighting


def sightings_view(request):
    """View for the sightings collection: showing a list of recent sightings
    (GET) as well as handling adding a new sighting (the POST action from
    the new-sighting form).
    """
    MAX_RECENT_SIGHTINGS = 50

    if request.method == 'POST':
        # Handle posting a new sighting to the sightings collection.
        if request.user.is_authenticated():
            form = SightingForm(request.POST)
            if form.is_valid():
                location = Location(user_input=form.cleaned_data['location'],
                                    latitude=form.cleaned_data['latitude'],
                                    longitude=form.cleaned_data['longitude'])
                location.save()

                identification = form.cleaned_data['identification']
                notes = form.cleaned_data['notes']
                location_notes = form.cleaned_data['location_notes']
                visibility = form.cleaned_data['visibility']
                sighting = Sighting(user=request.user,
                                    identification=identification,
                                    notes=notes, location=location,
                                    location_notes=location_notes,
                                    visibility=visibility)
                sighting.save()

                photo_ids = request.POST.getlist('sightings_photos')
                photos = ScreenedImage.objects.filter(id__in=photo_ids)
                sighting.photos.add(*photos)
                sighting.save()

                done_url = (reverse('ps-new-sighting-done') + '?s=%d'
                            % sighting.id)
                return HttpResponseRedirect(done_url)
            else:
                # Present the sighting form again for input correction.
                return _sighting_form_page(request, form)
        else:
            return HttpResponse(status=401)   # 401 Unauthorized
    elif request.method == 'GET':
        # Return a representation of the collection of sightings.
        sightings_queryset = Sighting.objects.select_related().all().\
            prefetch_related('location')
        sightings = []
        for sighting in sightings_queryset:

            may_show_sighting = _may_show_sighting(sighting, request.user)

            if may_show_sighting:
                created = sighting.created.strftime(SIGHTING_DAY_DATE_FORMAT)
                sightings.append({
                    'id': sighting.id,
                    'identification': sighting.identification,
                    'location': sighting.location,
                    'user': sighting.user,
                    'created': created,
                })
                if len(sightings) == MAX_RECENT_SIGHTINGS:
                    break

        return render_to_response('sightings.html', {
                    'sightings': sightings
               }, context_instance=RequestContext(request))
    else:
        # For an unsupported HTTP method, return Method Not Allowed.
        return HttpResponse(status=405)


def sightings_locator_view(request):
    return render_to_response('sightings_locator.html', {
                'map': SIGHTINGS_MAP_DEFAULTS
           }, context_instance=RequestContext(request))


def sighting_view(request, sighting_id):
    """View for an individual sighting. Supported HTTP methods: GET (return
    a sighting), POST (update an edited sighting), and DELETE (delete a
    sighting).
    """
    try:
        s = Sighting.objects.get(id=sighting_id)
    except ObjectDoesNotExist:
        raise Http404
    if request.method == 'GET':   # Show a sighting.

        # Determine if this sighting should be visible to this user.
        is_visible = False
        if s.visibility == 'PUBLIC':
            is_visible = True
        elif s.visibility == 'USERS':
            if request.user.is_authenticated():
                is_visible = True
            else:
                return redirect_to_login(request.path)
        #elif:
            # TODO: future support for a GROUPS visibility level
        elif s.visibility == 'PRIVATE':
            if (request.user.id == s.user.id) or request.user.is_staff:
                if request.user.is_authenticated():
                    is_visible = True
                else:
                    return redirect_to_login(request.path)

        if not is_visible:
            raise Http404

        SIGHTING_MAP_ZOOM = 14
        sighting = {
            'id': s.id,
            'identification': s.identification,
            'notes': s.notes,
            'location': s.location,
            'location_notes': s.location_notes,
            'user': s.user,
            'created': s.created.strftime(SIGHTING_DATE_TIME_FORMAT),
            'photos': s.private_photos()
        }
        return render_to_response('sighting.html', {
                    'sighting': sighting,
                    'map_zoom': SIGHTING_MAP_ZOOM,
               }, context_instance=RequestContext(request))
    elif request.method == 'POST':   # Update an edited sighting.
        if not request.user.is_authenticated():
            return HttpResponse(status=401)
        # Ensure this sighting belongs to the user requesting to update it.
        if s.user.id == request.user.id:
            form = SightingForm(request.POST)
            if form.is_valid():
                location = Location(user_input=form.cleaned_data['location'],
                                    latitude=form.cleaned_data['latitude'],
                                    longitude=form.cleaned_data['longitude'])
                location.save()
                s.location = location
                s.identification = form.cleaned_data['identification']
                s.notes = form.cleaned_data['notes']
                s.location_notes = form.cleaned_data['location_notes']
                s.visibility = form.cleaned_data['visibility']
                s.save()

                photo_ids = request.POST.getlist('sightings_photos')
                photos = ScreenedImage.objects.filter(id__in=photo_ids)
                existing_photo_ids = [photo.id for photo in s.photos.all()]
                for photo in photos.all():
                    if photo.id not in existing_photo_ids:
                        # This is a photo not included yet in the
                        # sighting, so add it.
                        s.photos.add(photo)
                s.save()

                done_url = (reverse('ps-edit-sighting-done') + '?s=%d'
                            % s.id)
                return HttpResponseRedirect(done_url)
            else:
                # Present the sighting form again for input correction.
                return _sighting_form_page(request, form, edit=True,
                                           sighting=s)
    elif request.method == 'DELETE':
        if not request.user.is_authenticated():
            return HttpResponse(status=401)   # 401 Unauthorized
        # Ensure this sighting belongs to the user requesting its deletion.
        if s.user.id == request.user.id:
            s.delete()
            # This response gets 200 OK, but subsequent responses will get 404
            # Not Found due to the record being gone.
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=403)   # 403 Forbidden
    else:
        # For an unsupported HTTP method, return Method Not Allowed.
        return HttpResponse(status=405)


@login_required
def new_sighting_view(request):
    """View for a blank form for posting a new sighting."""
    form = SightingForm()
    return _sighting_form_page(request, form)


@login_required
def new_sighting_done_view(request):
    """View for a confirmation page upon posting a new sighting."""
    return render_to_response('new_sighting_done.html', {
           }, context_instance=RequestContext(request))


@login_required
def manage_sightings_view(request):
    """View for a page where the user can review and edit their sightings."""
    sightings_queryset = Sighting.objects.filter(user=request.user).\
        select_related().prefetch_related('location')
    sightings = []
    for sighting in sightings_queryset:
        visibility = [item for item in SIGHTING_VISIBILITY_CHOICES
                      if item[0] == sighting.visibility][0][1]
        sightings.append({
            'id': sighting.id,
            'identification': sighting.identification,
            'location': sighting.location,
            'user': sighting.user,
            'created': sighting.created.strftime(SIGHTING_DATE_FORMAT),
            'visibility': visibility,
        })
    return render_to_response('manage_sightings.html', {
            'sightings': sightings,
        }, context_instance=RequestContext(request))


@login_required
def edit_sighting_view(request, sighting_id):
    """View for editing a sighting: the same form for posting a sighting,
    but with the fields filled in.
    """
    try:
        sighting = Sighting.objects.get(id=sighting_id)
    except ObjectDoesNotExist:
        return HttpResponse(status=404)
    # Ensure this sighting belongs to the user requesting to edit it.
    if sighting.user.id != request.user.id:
        return HttpResponse(status=403)   # 401 Forbidden
    form = SightingForm(initial={
        'identification': sighting.identification,
        'notes': sighting.notes,
        'location': sighting.location.id, # Set foreign key of Location record
        'location_notes': sighting.location_notes,
        'visibility': sighting.visibility,
    })
    return _sighting_form_page(request, form, edit=True, sighting=sighting)


@login_required
def edit_sighting_done_view(request):
    """View for a confirmation page upon editing a sighting."""
    return render_to_response('edit_sighting_done.html', {
           }, context_instance=RequestContext(request))


@login_required
def delete_sighting_view(request, sighting_id):
    """View for deleting a sighting: the contents of a lightbox dialog,
    using HTTP GET. (The actual delete should be performed by sending a
    HTTP DELETE request to the sighting URL.
    """
    s = Sighting.objects.get(id=sighting_id)
    if request.method == 'GET':
        sighting = {
            'id': s.id,
            'identification': s.identification,
            'notes': s.notes,
            'location': s.location,
            'location_notes': s.location_notes,
            'user': s.user,
            'created': s.created.strftime(SIGHTING_DATE_FORMAT),
        }
        return render_to_response('_delete_sighting.html', {
                'sighting': sighting
            }, context_instance=RequestContext(request))
    else:
        # For an unsupported HTTP method, return Method Not Allowed.
        return HttpResponse(status=405)


def questions_view(request):
    """View for the main Ask the Botanist page and the questions collection:
    showing a list of recent questions (GET) as well as handling adding a new
    question (the POST action from the question form).
    """
    MAX_RECENTLY_ANSWERED_QUESTIONS = 10
    max_question_length = Question._meta.get_field('question').max_length
    question_form = QuestionForm()
    upload_photo_form = ScreenedImageForm(initial={
        'image_type': 'QUESTION'
    })
    questions = _get_recently_answered_questions(
        MAX_RECENTLY_ANSWERED_QUESTIONS)

    return_ask_the_botanist_page = False

    if request.method == 'POST':
        # Handle posting a new question to the questions collection.
        if request.user.is_authenticated():
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                question_text = question_form.cleaned_data['question']
                question = Question(question=question_text,
                                    asked_by=request.user)
                question.save()

                image_ids = request.POST.getlist('question_images')
                images = ScreenedImage.objects.filter(id__in=image_ids)
                question.images.add(*images)
                question.save()

                done_url = reverse('ps-new-question-done')
                return HttpResponseRedirect(done_url)
            else:
                # Present the form again for input correction.
                return_ask_the_botanist_page = True
        else:
            return HttpResponse(status=401)   # 401 Unauthorized
    elif request.method == 'GET':
        # Return the main Ask the Botanist page.
        return_ask_the_botanist_page = True
    else:
        # For an unsupported HTTP method, return Method Not Allowed.
        return HttpResponse(status=405)

    if return_ask_the_botanist_page == True:
        return render_to_response('ask.html', {
                    'questions': questions,
                    'max_question_length': max_question_length,
                    'question_form': question_form,
                    'upload_photo_form': upload_photo_form
            }, context_instance=RequestContext(request))


def all_questions_view(request):
    """View for the full list of Questions and Answers."""
    questions = Question.objects.answered().order_by(
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
def checklist_index_view(request):
    """List of all of a user's visible checklists"""
    profile = request.user.userprofile
    all_checklists = profile.checklists

    return render_to_response('checklists.html', {
                'checklists': all_checklists,
           }, context_instance=RequestContext(request))


@login_required
def new_checklist_view(request):
    """Create a new checklist"""
    entry_image_form = ScreenedImageForm(initial={
        'image_type': 'CHECKLIST'
    })
    ChecklistEntryFormSet = _create_checklistentry_formset()
    if request.method == 'POST':
        profile = request.user.userprofile
        user_pod = profile.get_user_pod()
        checklist_form = ChecklistForm(request.POST)
        entry_formset = ChecklistEntryFormSet(request.POST)
        if checklist_form.is_valid() and entry_formset.is_valid():
            checklist = checklist_form.save()
            # Set the current user's personal pod as the owner
            owner = ChecklistCollaborator(collaborator=user_pod,
                   checklist=checklist, is_owner=True)
            owner.save()
            for entry in entry_formset.save(commit=False):
                entry.checklist = checklist
                entry.save()
            return redirect('ps-checklists')
    else:
        checklist_form = ChecklistForm()
        entry_formset = ChecklistEntryFormSet(
            queryset=ChecklistEntry.objects.none())

    return render_to_response('new_checklist.html', {
            'checklist_form': checklist_form,
            'entry_formset': entry_formset,
            'entry_image_form': entry_image_form,
           }, context_instance=RequestContext(request))


@login_required
def delete_checklists_view(request):
    if request.method == 'POST':
        delete_list = request.POST.getlist('checklist_id')
        deleted_lists = Checklist.objects.filter(pk__in=delete_list)
        deleted_lists.delete()

    # We only support POST for this - if someone does a GET for this
    # URL just send them back to the checklists page.
    return redirect('ps-checklists')


@login_required
def delete_checklist_view(request, checklist_id):
    """View for deleting a checklist by presenting a lightbox dialog,
    using HTTP GET. (The actual delete should be performed by sending a
    HTTP DELETE request to the sighting URL.
    """
    c = Checklist.objects.get(id=checklist_id)
    if request.method == 'GET':
        checklist = {
            'id': c.id,
            'name': c.name,
        }
        return render_to_response('_delete_checklist.html', {
                'checklist': checklist
            }, context_instance=RequestContext(request))
    else:
        # For an unsupported HTTP method, return Method Not Allowed.
        return HttpResponse(status=405)


@login_required
def export_checklist_view(request, checklist_id):
    response = HttpResponse(content_type='text/csv')
    checklist = get_object_or_404(Checklist, pk=checklist_id)
    filename = checklist.name.lower().replace(' ', '_') + '.csv'
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)

    writer = csv.writer(response)
    writer.writerow(('Plant Checklist Title:', checklist.name))
    writer.writerow(('Comments:', checklist.comments))
    writer.writerow([])
    writer.writerow(('Found?', 'Plant Name', 'Date Sighted', 'Location', 'Date Posted', 'Notes'))
    for entry in checklist.entries.all():
        found = 'Yes' if entry.is_checked else 'No'
        sighted = entry.date_found.strftime('%d/%m/%Y') if entry.date_found else 'N/A'
        posted = entry.date_posted.strftime('%d/%m/%Y') if entry.date_posted else 'N/A'
        writer.writerow((found, entry.plant_name, sighted, entry.location, posted, entry.note))

    return response

@login_required
def edit_checklist_view(request, checklist_id):
    """Edit a checklist"""
    entry_image_form = ScreenedImageForm(initial={
        'image_type': 'CHECKLIST'
    })
    ChecklistEntryFormSet = _create_checklistentry_formset(can_delete=True)
    checklist = get_object_or_404(Checklist, pk=checklist_id)
    if request.method == 'POST':
        checklist_form = ChecklistForm(request.POST, instance=checklist)
        entry_formset = ChecklistEntryFormSet(request.POST)
        if checklist_form.is_valid() and entry_formset.is_valid():
            checklist_form.save()
            for entry in entry_formset.save(commit=False):
                entry.checklist = checklist
                entry.save()
            return redirect('ps-checklists')
    else:
        checklist_form = ChecklistForm(instance=checklist)
        entry_formset = ChecklistEntryFormSet(
            queryset=ChecklistEntry.objects.filter(checklist=checklist))

    return render_to_response('edit_checklist.html', {
            'checklist': checklist,
            'checklist_form': checklist_form,
            'entry_formset': entry_formset,
            'entry_image_form': entry_image_form,
           }, context_instance=RequestContext(request))


@login_required
def checklist_view(request, checklist_id):
    """View for an individual checklist. Supported HTTP methods: GET (display
    a checklist) and DELETE (delete a checklist).
    """
    checklist = get_object_or_404(Checklist, pk=checklist_id)

    if request.method == 'GET':
        return render_to_response('checklist_detail.html', {
                'checklist': checklist
            }, context_instance=RequestContext(request))
    elif request.method == 'DELETE':
        if not request.user.is_authenticated():
            return HttpResponse(status=401)   # 401 Unauthorized
        # Ensure this checklist belongs to the user requesting its deletion.
        checklist_owner_profile = checklist.owner.get_owner()
        if checklist_owner_profile.user.id == request.user.id:
            checklist.delete()
            # This response gets 200 OK, but subsequent responses will get 404
            # Not Found due to the record being gone.
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=403)   # 403 Forbidden
    else:
        # For an unsupported HTTP method, return Method Not Allowed.
        return HttpResponse(status=405)

@login_required
def find_people_view(request):
    """View for the Find People results page."""
    MIN_QUERY_LENGTH = 2
    query = request.GET.get('n', '').lower()
    people = []
    if len(query) >= MIN_QUERY_LENGTH:
        candidates = UserProfile.objects.filter(
            Q(display_name__icontains=query) |
            Q(user__username__istartswith=query)).order_by('display_name')
        for candidate in candidates:
            is_match = False

            # Figure out if we can show the display name to this user.
            # TODO: later when available, take 'GROUPS' setting into account.
            may_show_display_name = (request.user.is_staff or
                (candidate.details_visibility != 'PRIVATE'))

            # If a user has specified a display name, check it.
            if may_show_display_name and candidate.display_name != '':
                # Check the beginning of any parts of the display name.
                parts = candidate.display_name.lower().split(' ')
                for part in parts:
                    if part.startswith(query):
                        is_match = True
                        break
            # Check the beginning of the username.
            if candidate.user.username.lower().startswith(query):
                is_match = True
            if is_match:
                people.append(candidate)

    return render_to_response('find_people.html', {
            'min_query_length': MIN_QUERY_LENGTH,
            'name_query': query,
            'people': people,
        }, context_instance=RequestContext(request))


@login_required
def find_people_profile_view(request, username):
    user = None
    profile = None
    details_visible = False
    location_visible = False
    try:
        user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        pass
    if user:
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            pass

    if profile:
        if profile.details_visibility == 'PRIVATE':
            if request.user.id == user.id or request.user.is_staff:
                details_visible = True
        elif profile.details_visibility == 'USERS':
            details_visible = True

        if profile.location_visibility == 'PRIVATE':
            if request.user.id == user.id or request.user.is_staff:
                location_visible = True
        elif profile.location_visibility == 'USERS':
            location_visible = True

    return render_to_response('_find_people_profile.html', {
            'profile': profile,
            'username': username,
            'details_visible': details_visible,
            'location_visible': location_visible,
        }, context_instance=RequestContext(request))


@login_required
def your_profile_view(request):
    """View for the logged-in user's profile."""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None

    profile_form = UserProfileForm(instance=profile)
    avatar_form = ScreenedImageForm(initial={
        'image_type': 'AVATAR'
    })

    DEFAULT_LOCATION = "Rumford, ME"
    location = profile.location if profile.location else DEFAULT_LOCATION

    context = {
        'profile_form': profile_form,
        'avatar_form': avatar_form,
        'location': location,
    }
    return render_to_response('your_profile.html', context,
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
        deleted=False, orphaned=False).exclude(
            image_type='QUESTION')   # No screening here for question images
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
        profile, created = UserProfile.objects.get_or_create(
            user=request.user)
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
                'info': 'Form Validation error:\n{0}'.format(
                    profile_form.errors.as_text())
            }), mimetype='application/json')

    return HttpResponse(simplejson.dumps({'success': True}),
                                         mimetype='application/json')


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

            # Return basic information in the response, as well as
            # latitude and longitude if the original image contained GPS
            # coordinates in its metadata.
            latitude = None
            longitude = None
            if new_image.latitude is not None:
                latitude = float(new_image.latitude) # convert so serializable
            if new_image.longitude is not None:
                longitude = float(new_image.longitude)
            response.update({
                'id': new_image.pk,
                'thumb': new_image.thumb.url,
                'url': new_image.image.url,
                'latitude': latitude,
                'longitude': longitude
            })

    return HttpResponse(simplejson.dumps(response),
                        mimetype='application/json')


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

    sightings = Sighting.objects.select_related().all().\
        prefetch_related('location').order_by('-created')
    if plant_name:
        sightings = sightings.filter(identification__iexact=plant_name)

    sightings_json = []
    for sighting in sightings:

        may_show_sighting = _may_show_sighting(sighting, request.user)

        if may_show_sighting:
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
                'identification': sighting.identification,
                'created': unicode(sighting.created.strftime(
                                   SIGHTING_DATE_FORMAT)),
                'location': sighting.location.user_input,
                'latitude': sighting.location.latitude,
                'longitude': sighting.location.longitude,
                'user': sighting.user.username, # TODO: fast way of getting
                                                #       user display name
                'description': sighting.notes,
                'photos': photos,
            })

            if len(sightings_json) == MAX_TO_RETURN:
                break

    json = {
        'sightings': sightings_json
    }

    return HttpResponse(simplejson.dumps(json),
                        mimetype='application/json; charset=utf-8')


@login_required
def ajax_people_suggestions(request):
    """Return suggestions with names to help users find other users."""
    MIN_QUERY_LENGTH = 1
    MAX_RESULTS = 10
    MIN_SUGGESTION_LENGTH = 2
    query = request.GET.get('q', '').lower()
    suggestions = []
    ordered_suggestions = []

    if len(query) >= MIN_QUERY_LENGTH:
        # Get all potentially matching display names and usernames.
        names = UserProfile.objects.filter(
                    Q(display_name__icontains=query) |
                    Q(user__username__istartswith=query))

        for name in names:
            if len(suggestions) == MAX_RESULTS:
                break

            # Figure out if we can show the display name to this user.
            # TODO: later when available, take into account 'GROUPS' setting.
            may_show_display_name = (name.details_visibility != 'PRIVATE')

            display_name = name.display_name.lower()
            if may_show_display_name and display_name != '':
                # Add each part (first, last, etc.) of the display name.
                parts = display_name.split(' ')
                for part in parts:
                    part = part.strip('.')   # for initials, abbreviations
                    if len(part) < MIN_SUGGESTION_LENGTH:
                        continue
                    if part.startswith(query) and part not in suggestions:
                            suggestions.append(part)
                            if len(suggestions) < MAX_RESULTS:
                                break

        # If there is room in the suggestions list, may add usernames.
        # Although username does not show on pages if a display name takes
        # its place, it does show in the profile link URL. Users might know
        # or exchange usernames informally and expect to see them listed.
        if len(suggestions) < MAX_RESULTS:
            for name in names:
                username = name.user.username.lower()
                if username.find(query) > -1 and username not in suggestions:
                    suggestions.append(username)
                    if len(suggestions) == MAX_RESULTS:
                        break

        # Order the suggestions so any that start with the query string
        # appear first.
        suggestions = sorted(suggestions)
        for suggestion in reversed(suggestions):
            if suggestion.startswith(query):
                ordered_suggestions.insert(0, suggestion)
            else:
                ordered_suggestions.append(suggestion)

    return HttpResponse(simplejson.dumps(ordered_suggestions),
                        mimetype='application/json; charset=utf-8')


@login_required
def ajax_restrictions(request):
    """API call for determining whether a sighting should be restricted
    to private and staff viewing only for plants with a conservation
    concern.

    Most of the time only one plant will be returned, but in some cases
    such as where more than one plant has the same common name, multiple
    plants can be returned. The caller should look at all the
    'sightings_restricted' values, and if *any* are marked True, then
    do restrict sightings for that plant name.
    """
    restrictions_info = []
    plant_name = request.GET.get('plant')
    location = request.GET.get('location')
    if plant_name:
        restrictions_info = restrictions(plant_name, location)
    return HttpResponse(simplejson.dumps(restrictions_info),
                        mimetype='application/json; charset=utf-8')
