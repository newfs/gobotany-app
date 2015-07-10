import csv
import json
import math

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group, User
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
from django.utils.timezone import utc

import emailconfirmation_views
from emailconfirmation_models import EmailConfirmation

from gobotany.plantshare.forms import (ChangeEmailForm, ChecklistEntryForm,
    ChecklistForm, QuestionForm, ScreenedImageForm, SightingForm,
    UserProfileForm)
from gobotany.plantshare.models import (Checklist, ChecklistCollaborator,
    ChecklistEntry, Location, Question, ScreenedImage, Sighting,
    SIGHTING_VISIBILITY_CHOICES, UserProfile)
from gobotany.plantshare.utils import prior_signup_detected, restrictions

SIGHTINGS_MAP_DEFAULTS = {
    'latitude': '43.66',
    'longitude': '-70.27',
    'center_title': 'Portland, Maine',
    'zoom': '7'
}

SIGHTING_DATE_FORMAT = '%B %e'
SIGHTING_DATE_YEAR_FORMAT = SIGHTING_DATE_FORMAT + ' %Y'
SIGHTING_SHORT_DATE_YEAR_FORMAT = '%e %b %Y'
SIGHTING_DAY_DATE_FORMAT = '%A, ' + SIGHTING_DATE_FORMAT


# Function and decorator for determining if a logged-in PlantShare user
# has accepted the PlantShare Terms of Agreement and therefore can use
# the PlantShare section of the site with member priveleges.

def logged_in_user_agreed_to_terms(user):
    if user and user.is_authenticated():
        agreed_to_terms = user.groups.filter(
            name=settings.AGREED_TO_TERMS_GROUP).exists()
        return agreed_to_terms
    else:
        return True   # agreement not required now

# This decorator should be used on all views that also use the
# @login_required decorator. That is, if login is required for a view,
# acceptance of the Terms of Agreement is required too.
# However, this decorator can be used without login being required, such
# as is the case for any PlantShare pages that do show some content
# without requiring a logged-in PlantShare user (such as the PlantShare
# main page, etc.).
def terms_agreed_on_login(function=None):
    decorator = user_passes_test(logged_in_user_agreed_to_terms,
        login_url=reverse_lazy('ps-terms-of-agreement'))
    if function:
        return decorator(function)
    return decorator


def _sighting_form_page(request, form, edit=False, sighting=None):
    """Return a sighting form, either blank or with data."""
    template = 'new_sighting.html'
    if edit == True:
        template = 'edit_sighting.html'

    upload_photo_form = ScreenedImageForm(initial={
        'image_type': 'SIGHTING'
    })
    if sighting:
        upload_photo_form = ScreenedImageForm(initial={
            'image_type': 'SIGHTING'
        })

    return render(request, template, {
               'form': form,
               'upload_photo_form': upload_photo_form,
               'sighting': sighting,
           }, context_instance=RequestContext(request))


def _create_checklistentry_formset(extra=0, **kwargs):
    return modelformset_factory(ChecklistEntry, form=ChecklistEntryForm,
            extra=extra, **kwargs)


# Views

@login_required
def terms_of_agreement_view(request):
    return render_to_response('terms_of_agreement.html', {
        }, context_instance=RequestContext(request))


@login_required
def terms_of_agreement_accept_view(request):
    """Handle the form submission for accepting the Terms of Agreement."""
    if request.method == 'POST':
        REQUIRED_VALUES = ['terms1', 'terms2', 'terms3', 'terms4']
        checked_values = request.POST.getlist('terms')
        if (set(checked_values) == set(REQUIRED_VALUES)):
            # All the check boxes are checked, so the user has agreed
            # to the Terms. Place them in a Group that signifies this.
            group = Group.objects.get(name=settings.AGREED_TO_TERMS_GROUP)
            group.user_set.add(request.user)
            # Verify the user is now in the group.
            users = group.user_set.all()
            user_in_group = request.user in users
            if user_in_group:
                url = 'ps-main'   # default: named URL for redirect
                if 'next' in request.POST:
                    # Redirect to the URL from the 'next' variable.
                    url = request.POST['next']
                return redirect(url)
            else:
                # Somehow the user did not get added to the group.
                # Return to the form.
                return redirect('ps-terms-of-agreement')
        else:
            # Not all check boxes were checked, so return to the form.
            return redirect('ps-terms-of-agreement')
    else:
        return HttpResponse(status=405)   # HTTP method not allowed


def _get_recently_answered_questions(number_of_questions):
    questions = Question.objects.answered().order_by(
        '-answered')[:number_of_questions]
    return questions


def _get_recent_sightings(request, profile):
    MAX_RECENT_SIGHTINGS = 20
    recent_sightings = []

    # Get the sightings with approved photos.
    if profile:
        # Also include any sightings the current user posted where the
        # photos may not have been screened and approved yet (because
        # it's always OK to show a user's own photos to that user).
        sightings_with_photos = Sighting.objects.filter(
            Q(photos__isnull=False, photos__is_approved=True) |
            Q(photos__isnull=False, user=profile.user)).order_by(
            '-created').distinct('created')
    else:
        sightings_with_photos = Sighting.objects.filter(
            photos__isnull=False, photos__is_approved=True).order_by(
            '-created').distinct('created')

    for sighting in sightings_with_photos:
        may_show_sighting = _may_show_sighting(sighting, request.user)
        if may_show_sighting:
            recent_sightings.append(sighting)
            if len(recent_sightings) == MAX_RECENT_SIGHTINGS:
                break

    return recent_sightings


@terms_agreed_on_login
def plantshare_view(request):
    """View for the main PlantShare page."""
    upload_photo_form = ScreenedImageForm(initial={
        'image_type': 'QUESTION'
    })
    MAX_RECENTLY_ANSWERED_QUESTIONS = 3
    questions = _get_recently_answered_questions(
                MAX_RECENTLY_ANSWERED_QUESTIONS)
    max_question_length = Question._meta.get_field('question').max_length

    avatar_info = UserProfile.default_avatar_image()
    profile = None
    if request.user.is_authenticated():
        try:
            profile = UserProfile.objects.get(user=request.user)
            avatar_info = profile.private_avatar_image()
        except UserProfile.DoesNotExist:
            avatar_info = UserProfile.default_avatar_image()

    recent_sightings = _get_recent_sightings(request, profile)

    sightings_count = 0
    checklists_count = 0
    if profile:
        sightings_count = Sighting.objects.filter(
            user=profile.user).count()
        checklists_count = profile.checklists.count()

    return render_to_response('plantshare.html', {
                'prior_signup_detected': prior_signup_detected(request),
                'avatar': avatar_info,
                'map': SIGHTINGS_MAP_DEFAULTS,
                'questions': questions,
                'max_questions': MAX_RECENTLY_ANSWERED_QUESTIONS,
                'max_question_length': max_question_length,
                'upload_photo_form': upload_photo_form,
                'profile': profile,
                'recent_sightings': recent_sightings,
                'sightings_count': sightings_count,
                'checklists_count': checklists_count,
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


def _get_photo_for_thumbnail(sighting, request):
    """Look for a photo that can be used for a thumbnail image for a
    sighting on the Recent Sightings page or sightings by year pages.
    """
    photo = ''
    for p in sighting.photos.all():
        # If the photo is approved, or the user viewing the page
        # is the owner of the sighting photo, show the photo.
        if p.is_approved or (sighting.user == request.user):
            photo = p
            break
    return photo


def _get_display_names(sightings_queryset):
    """Get a list of tuples of user ids and display names for a queryset
    of sightings.
    """
    user_ids = set()
    for sighting in sightings_queryset:
        user_ids.add(sighting.user.id)
    display_names = UserProfile.objects.filter(
        user__id__in=user_ids).values_list('user__id', 'display_name')
    return display_names

def _get_user_display_name(display_names, sighting):
    user_display_name = None
    for display_name in display_names:
        if int(display_name[0]) == sighting.user.id:
            user_display_name = display_name[1]
            break
    return user_display_name


@terms_agreed_on_login
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
                date_time = form.cleaned_data['created']
                # Add the current time in case the user changed the date,
                # just for ordering entries as they were posted.
                now = datetime.utcnow().replace(tzinfo=utc)
                date_time = date_time + timedelta(
                    hours=now.hour, minutes=now.minute)
                created = date_time
                notes = form.cleaned_data['notes']
                location_notes = form.cleaned_data['location_notes']
                visibility = form.cleaned_data['visibility']
                flagged = form.cleaned_data['flagged']
                approved = form.cleaned_data['approved']
                sighting = Sighting(user=request.user,
                                    identification=identification,
                                    created=created,
                                    notes=notes, location=location,
                                    location_notes=location_notes,
                                    visibility=visibility,
                                    flagged=flagged,
                                    approved=approved)
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
            prefetch_related('location', 'photos', 'user')
        display_names = _get_display_names(sightings_queryset)

        sightings = []
        for sighting in sightings_queryset:
            may_show_sighting = _may_show_sighting(sighting, request.user)
            if may_show_sighting:
                photo = _get_photo_for_thumbnail(sighting, request)
                created = sighting.created.strftime(SIGHTING_DATE_FORMAT)
                year = sighting.created.strftime('%Y')
                user_display_name = _get_user_display_name(display_names,
                    sighting)
                sightings.append({
                    'id': sighting.id,
                    'photo': photo,
                    'identification': sighting.identification,
                    'location': sighting.location,
                    'user': sighting.user,
                    'user_display_name': user_display_name,
                    'created': created,
                    'year': year,
                })
                if len(sightings) == MAX_RECENT_SIGHTINGS:
                    break

        years = [dt.year for dt in
            Sighting.objects.datetimes('created', 'year', order='DESC')]

        return render_to_response('sightings.html', {
                    'sightings': sightings,
                    'years': years,
               }, context_instance=RequestContext(request))
    else:
        # For an unsupported HTTP method, return Method Not Allowed.
        return HttpResponse(status=405)


@terms_agreed_on_login
def sightings_by_year_view(request, year):
    sightings_queryset = Sighting.objects.select_related().\
        filter(created__year=year).prefetch_related('location', 'photos',
        'user')
    display_names = _get_display_names(sightings_queryset)

    sightings = []
    for sighting in sightings_queryset:
        may_show_sighting = _may_show_sighting(sighting, request.user)
        if may_show_sighting:
            photo = _get_photo_for_thumbnail(sighting, request)
            created = sighting.created.strftime(SIGHTING_DATE_FORMAT)
            user_display_name = _get_user_display_name(display_names,
                sighting)
            sightings.append({
                'id': sighting.id,
                'photo': photo,
                'identification': sighting.identification,
                'location': sighting.location,
                'user': sighting.user,
                'user_display_name': user_display_name,
                'created': created,
            })

    years = [str(dt.year) for dt in
        Sighting.objects.datetimes('created', 'year', order='DESC')]

    if year in years:
        return render_to_response('sightings_by_year.html', {
                    'year': year,
                    'sightings': sightings,
                    'years': years,
               }, context_instance=RequestContext(request))
    else:
        raise Http404


@terms_agreed_on_login
def sightings_locator_view(request):
    profile = None
    if request.user.is_authenticated():
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            pass
    recent_sightings = _get_recent_sightings(request, profile)
    return render_to_response('sightings_locator.html', {
                'map': SIGHTINGS_MAP_DEFAULTS,
                'recent_sightings': recent_sightings,
           }, context_instance=RequestContext(request))


@terms_agreed_on_login
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

        photos = s.approved_photos()
        if s.user == request.user:
            # If the current user made this sighting, show the photos
            # even if they have not yet been screened and approved.
            photos = s.private_photos()

        sighting = {
            'id': s.id,
            'identification': s.identification,
            'notes': s.notes,
            'location': s.location,
            'location_notes': s.location_notes,
            'user': s.user,
            'created': s.created.strftime(SIGHTING_DATE_YEAR_FORMAT),
            'year': s.created.year,
            'photos': photos
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
                updated_date_time = form.cleaned_data['created']
                # Add the current time, just for ordering entries as
                # they were edited.
                now = datetime.utcnow().replace(tzinfo=utc)
                updated_date_time = updated_date_time + timedelta(
                    hours=now.hour, minutes=now.minute)
                s.created = updated_date_time
                s.notes = form.cleaned_data['notes']
                s.location_notes = form.cleaned_data['location_notes']
                s.visibility = form.cleaned_data['visibility']
                s.flagged = form.cleaned_data['flagged']
                s.approved = form.cleaned_data['approved']
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
@terms_agreed_on_login
def new_sighting_view(request):
    """View for a blank form for posting a new sighting."""
    now = datetime.utcnow().replace(tzinfo=utc)
    form = SightingForm(initial={
        'created': now
    })
    return _sighting_form_page(request, form)


@login_required
@terms_agreed_on_login
def new_sighting_done_view(request):
    """View for a confirmation page upon posting a new sighting."""
    return render_to_response('new_sighting_done.html', {
           }, context_instance=RequestContext(request))


@login_required
@terms_agreed_on_login
def manage_sightings_view(request):
    """View for a page where the user can review and edit their sightings."""
    sightings_queryset = Sighting.objects.filter(user=request.user).\
        select_related().prefetch_related('location')
    sightings = []
    for sighting in sightings_queryset:
        visibility = [item for item in SIGHTING_VISIBILITY_CHOICES
                      if item[0] == sighting.visibility][0][1]
        photo = ''
        if sighting.approved_photos():
            photo = sighting.approved_photos()[0]
        sightings.append({
            'id': sighting.id,
            'photo': photo,
            'identification': sighting.identification,
            'location': sighting.location,
            'user': sighting.user,
            'created': sighting.created.strftime(SIGHTING_DATE_YEAR_FORMAT),
            'visibility': visibility,
        })
    return render_to_response('manage_sightings.html', {
            'sightings': sightings,
        }, context_instance=RequestContext(request))


@login_required
@terms_agreed_on_login
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
        'location': sighting.location.id, # Set foreign key of Location record
        'location_notes': sighting.location_notes,
        'latitude': sighting.location.latitude,
        'longitude': sighting.location.longitude,
        'created': sighting.created,
        'notes': sighting.notes,
        'visibility': sighting.visibility,
        'flagged': sighting.flagged,
        'approved': sighting.approved
    })
    return _sighting_form_page(request, form, edit=True, sighting=sighting)


@login_required
@terms_agreed_on_login
def edit_sighting_done_view(request):
    """View for a confirmation page upon editing a sighting."""
    return render_to_response('edit_sighting_done.html', {
           }, context_instance=RequestContext(request))


@login_required
@terms_agreed_on_login
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


@terms_agreed_on_login
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


@terms_agreed_on_login
def all_questions_by_year_view(request, year=None):
    """View for a list of all Questions and Answers for a year."""

    years = [str(dt.year) for dt in
        Question.objects.datetimes('asked', 'year', order='DESC')]
    # If this view was not called with a year, use the latest year.
    if not year:
        year = years[0]

    # If this view was called with a q?= parameter, look up the year
    # of the question id in the database and redirect to that year. This
    # is to handle redirects from the client side for old-format URLs.
    question_id = request.GET.get('q', None)
    if (question_id):
        question_id = int(question_id)
        question = get_object_or_404(Question, pk=question_id)
        if question:
            if question.answered:
                year = question.asked.year
                url = reverse('ps-all-questions-by-year', args=(year,))
                return HttpResponseRedirect(url)
            else:
                raise Http404

    questions = Question.objects.answered().filter(
        asked__year=year).order_by('-answered')

    if questions:
        return render_to_response('all_questions.html', {
                'questions': questions,
                'year': year,
                'years': years
            }, context_instance=RequestContext(request))
    else:
        raise Http404


@login_required
@terms_agreed_on_login
def new_question_done_view(request):
    """View for a confirmation page upon asking a new question."""
    return render_to_response('new_question_done.html', {
           }, context_instance=RequestContext(request))


@login_required
@terms_agreed_on_login
def checklist_index_view(request):
    """List of all of a user's visible checklists"""
    profile = request.user.userprofile
    all_checklists = profile.checklists

    return render_to_response('checklists.html', {
                'checklists': all_checklists,
           }, context_instance=RequestContext(request))


@login_required
@terms_agreed_on_login
def new_checklist_view(request):
    """Create a new checklist"""
    entry_image_form = ScreenedImageForm(initial={
        'image_type': 'CHECKLIST'
    })
    ChecklistEntryFormSet = _create_checklistentry_formset(extra=1)
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
@terms_agreed_on_login
def delete_checklists_view(request):
    if request.method == 'POST':
        delete_list = request.POST.getlist('checklist_id')
        deleted_lists = Checklist.objects.filter(pk__in=delete_list)
        deleted_lists.delete()

    # We only support POST for this - if someone does a GET for this
    # URL just send them back to the checklists page.
    return redirect('ps-checklists')


@login_required
@terms_agreed_on_login
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
@terms_agreed_on_login
def export_checklist_view(request, checklist_id):
    response = HttpResponse(content_type='text/csv')
    checklist = get_object_or_404(Checklist, pk=checklist_id)
    filename = checklist.name.lower().replace(' ', '_') + '.csv'
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(
        filename)

    writer = csv.writer(response)
    writer.writerow(('Plant Checklist Title:', checklist.name))
    writer.writerow(('Comments:', checklist.comments))
    writer.writerow([])
    writer.writerow(('Found?', 'Plant Name', 'Date Sighted', 'Location',
        'Date Posted', 'Notes'))
    for entry in checklist.entries.all():
        found = 'Yes' if entry.is_checked else 'No'
        sighted = (entry.date_found.strftime('%d/%m/%Y')
            if entry.date_found else 'N/A')
        posted = (entry.date_posted.strftime('%d/%m/%Y')
            if entry.date_posted else 'N/A')
        writer.writerow((found, entry.plant_name, sighted, entry.location,
            posted, entry.note))

    return response

@login_required
@terms_agreed_on_login
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
@terms_agreed_on_login
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


def _may_show_display_name(request, user_profile):
    """Determine if a user's display name may be shown to the current user:
    Show if the user's visibility is not set to private, or if the name
    belongs to the current user, or if the current user is a 'staff' user.
    TODO: later when available, take into account a 'GROUPS' setting.
    """
    may_show = ((user_profile.details_visibility != 'PRIVATE') or
                (user_profile.user.id == request.user.id) or
                (request.user.is_staff == True))
    return may_show


@login_required
@terms_agreed_on_login
def find_people_view(request):
    """View for the Find People results page."""
    MIN_QUERY_LENGTH = 2
    query = request.GET.get('n', '')
    query_l = query.lower()
    people = []
    if len(query) >= MIN_QUERY_LENGTH:
        candidates = UserProfile.objects.filter(
            Q(display_name__icontains=query_l) |
            Q(user__username__istartswith=query_l)).order_by('display_name')
        for candidate in candidates:
            is_match = False
            may_show_display_name = _may_show_display_name(request, candidate)

            # If a user has specified a display name, check it.
            if may_show_display_name and candidate.display_name != '':
                # Check the beginning of any parts of the display name.
                parts = candidate.display_name.lower().split(' ')
                for part in parts:
                    if part.startswith(query_l):
                        is_match = True
                        break
                # Also check the entire display name.
                if candidate.display_name.lower().startswith(query_l):
                    is_match = True
            # Check the beginning of the username.
            if candidate.user.username.lower().startswith(query_l):
                is_match = True
            if is_match:
                people.append(candidate)

    return render_to_response('find_people.html', {
            'min_query_length': MIN_QUERY_LENGTH,
            'name_query': query,
            'people': people,
        }, context_instance=RequestContext(request))


@login_required
@terms_agreed_on_login
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
@terms_agreed_on_login
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

    password_exists = False
    email_address_exists = False
    change_password_form = None
    change_email_form = None
    if profile:
        password_exists = (len(profile.user.password) > 0)
        email_address_exists = (len(profile.user.email) > 0)
        change_password_form = PasswordChangeForm(data=None,
            user=profile.user)
        change_email_form = ChangeEmailForm(data=None, user=profile.user)

    context = {
        'profile_form': profile_form,
        'avatar_form': avatar_form,
        'location': location,
        'password_exists': password_exists,
        'email_address_exists': email_address_exists,
        'form': change_password_form,   # named as another view used expects
        'change_email_form': change_email_form,
    }
    return render_to_response('your_profile.html', context,
            context_instance=RequestContext(request))


@login_required
def change_email(request):
    if request.method not in ['GET', 'POST']:
        return HttpResponse(status=405)   # HTTP method not allowed

    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        change_email_form = ChangeEmailForm(request.POST, user=profile.user)
        if change_email_form.is_valid():
            # Create an EmailAddress record and send confirmation email.
            change_email_form.save()
            url = reverse('ps-change-email-confirmation-sent')
            return HttpResponseRedirect(url)
    else:
        change_email_form = ChangeEmailForm(user=profile.user)

    context = {
        'change_email_form': change_email_form,
    }

    return render_to_response('emailconfirmation/change_email_address.html',
        context, context_instance=RequestContext(request))


@login_required
def change_email_confirmation_sent(request):
    return render_to_response(
        'emailconfirmation/change_email_confirmation_sent.html',
        {}, context_instance=RequestContext(request))


# Patch the emailconfirmation view 'confirm_email' to make it require
# that the user be logged in.
@login_required
def confirm_email(request, confirmation_key):
    confirmation_key = confirmation_key.lower()
    email_address = EmailConfirmation.objects.confirm_email(confirmation_key)
    return render_to_response('emailconfirmation/confirm_email.html', {
        'email_address': email_address,
    }, context_instance=RequestContext(request))

emailconfirmation_views.confirm_email = confirm_email


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
            form.instance.screened = datetime.utcnow().replace(tzinfo=utc)
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
        return HttpResponse(json.dumps({
            'error': True,
            'info': 'User is not authenticated.'
        }), content_type='application/json')

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
            return HttpResponse(json.dumps({
                'error': True,
                'info': 'Form Validation error:\n{0}'.format(
                    profile_form.errors.as_text())
            }), content_type='application/json')

    return HttpResponse(json.dumps({'success': True}),
                                         content_type='application/json')


def ajax_image_upload(request):
    """ Ajax form submission of image upload form """
    if not request.user.is_authenticated():
        return HttpResponse(json.dumps({
            'error': True,
            'info': 'Authentication error'
        }), content_type='application/json')

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

    return HttpResponse(json.dumps(response),
                        content_type='application/json')


def ajax_image_reject(request, image_id):
    """ Reject an image that was previously uploaded. """
    if not request.user.is_authenticated():
        return HttpResponse(json.dumps({
            'error': True,
            'info': 'Authentication error'
        }), content_type='application/json')

    image = ScreenedImage.objects.get(pk=image_id)

    # Only staff or the user who originally uploaded the image may reject it.
    if not (request.user.is_staff or request.user == image.uploaded_by):
        return HttpResponse(json.dumps({
            'error': True,
            'info': 'Authentication error'
        }), content_type='application/json')

    image.is_approved = False
    image.screened = datetime.utcnow().replace(tzinfo=utc)
    image.screened_by = request.user

    image.save()

    response = {
        'success': True
    }

    return HttpResponse(json.dumps(response), content_type='application/json')


def ajax_sightings(request):
    """Return sightings data: the most recent sightings, or the most
    recent sightings for a plant name, or a recent sighting by sighting id.
    """

    MAX_TO_RETURN = 100
    plant_name = request.GET.get('plant')
    sighting_id = request.GET.get('id')

    sightings = Sighting.objects.select_related().all().\
        prefetch_related('location').order_by('-created')
    if plant_name:
        sightings = sightings.filter(identification__iexact=plant_name)
    elif sighting_id:
        sightings = sightings.filter(id=sighting_id)

    sightings_json = []
    for sighting in sightings:

        may_show_sighting = _may_show_sighting(sighting, request.user)

        if may_show_sighting:
            photos = []
            for photo in sighting.approved_photos():
                photos.append(photo.thumb_cropped.url)

            # If the location coordinates are not valid numbers,
            # set them to None, which converts to null in the JSON.
            latitude = None
            longitude = None
            location_user_input = None
            if sighting.location and sighting.location.latitude and \
                sighting.location.longitude:

                latitude = sighting.location.latitude
                if math.isnan(latitude):
                    latitude = None
                longitude = sighting.location.longitude
                if math.isnan(longitude):
                    longitude = None
                location_user_input = sighting.location.user_input

            sightings_json.append({
                'id': sighting.id,
                'identification': sighting.identification,
                'created': unicode(sighting.created.strftime(
                                   SIGHTING_SHORT_DATE_YEAR_FORMAT)),
                'location': location_user_input,
                'latitude': latitude,
                'longitude': longitude,
                'user': sighting.user.username, # TODO: fast way of getting
                                                #       user display name
                'description': sighting.notes,
                'photos': photos,
            })

            if len(sightings_json) == MAX_TO_RETURN:
                break

    output = {
        'sightings': sightings_json
    }

    return HttpResponse(json.dumps(output),
                        content_type='application/json; charset=utf-8')


@login_required
@terms_agreed_on_login
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

            may_show_display_name = _may_show_display_name(request, name)
            display_name = name.display_name
            if may_show_display_name and display_name != '':
                # Add each part (first, last, etc.) of the display name.
                parts = display_name.split(' ')
                for part in parts:
                    part = part.strip('.')   # for initials, abbreviations
                    if len(part) < MIN_SUGGESTION_LENGTH:
                        continue
                    if (part.lower().startswith(query) and
                        part not in suggestions):
                            suggestions.append(part)
                            if len(suggestions) < MAX_RESULTS:
                                break
                # Also match against the entire display name.
                if (display_name.lower().startswith(query) and
                    display_name not in suggestions):

                    suggestions.append(display_name)

        # If there is room in the suggestions list, add usernames.
        # Although username does not show on pages if a display name takes
        # its place, it does show in the profile link URL. Users might know
        # or exchange usernames informally and expect to see them listed.
        if len(suggestions) < MAX_RESULTS:
            for name in names:
                username = name.user.username
                if (username.lower().find(query) > -1 and
                    username not in suggestions):

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

    return HttpResponse(json.dumps(ordered_suggestions),
                        content_type='application/json; charset=utf-8')


@login_required
@terms_agreed_on_login
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
    return HttpResponse(json.dumps(restrictions_info),
                        content_type='application/json; charset=utf-8')
