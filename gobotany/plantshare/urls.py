from django.urls import include, path, re_path

from gobotany.plantshare import views

urlpatterns = [
    # PlantShare main page
    path('', views.plantshare_view, name='ps-main'),

    # Normal registration login
    path('accounts/', include('gobotany.plantshare.backends.default.urls')),

    # Terms of Agreement
    path('terms-of-agreement/accept/', views.terms_of_agreement_accept_view,
        name='ps-terms-of-agreement-accept'),
    path('terms-of-agreement/', views.terms_of_agreement_view,
        name='ps-terms-of-agreement'),

    # Post a (new) Sighting form
    path('sightings/new/', views.new_sighting_view, name='ps-new-sighting'),
    path('sightings/new/done/', views.new_sighting_done_view,
        name='ps-new-sighting-done'),

    # Sightings Locator
    path('sightings/locator/', views.sightings_locator_view,
        name='ps-sightings-locator'),

    # Manage Your Sightings
    path('sightings/manage/', views.manage_sightings_view,
        name='ps-manage-sightings'),
    path('sightings/<int:sighting_id>/edit/',
        views.edit_sighting_view, name='ps-edit-sighting'),
    path('sightings/edit/done/', views.edit_sighting_done_view,
        name='ps-edit-sighting-done'),
    path('sightings/<int:sighting_id>/delete/',
        views.delete_sighting_view, name='ps-delete-sighting'),
    path('sightings/<int:sighting_id>/', views.sighting_view,
        name='ps-sighting'),

    # Recent Sightings, and sightings by year
    path('sightings/', views.sightings_view, name='ps-sightings'),
    re_path(r'^sightings/year-(?P<year>[0-9]{4})/$',
        views.sightings_by_year_view, name='ps-sightings-by-year'),

    # Ask the Botanist
    path('questions/', views.questions_view, name='ps-questions'),
    path('questions/new/done/', views.new_question_done_view,
        name='ps-new-question-done'),
    re_path(r'^questions/all/(?P<year>[0-9]{4})/$',
        views.all_questions_by_year_view,
        name='ps-all-questions-by-year'),
    path('questions/all/', views.all_questions_by_year_view,
        name='ps-all-questions'),

    # Checklists
    path('checklists/', views.checklist_index_view, name='ps-checklists'),
    path('checklists/new/', views.new_checklist_view,
        name='ps-checklist-new'),
    path('checklists/delete/', views.delete_checklists_view,
        name='ps-checklists-delete'),
    path('checklists/<int:checklist_id>/', views.checklist_view,
        name='ps-checklist'),
    path('checklists/<int:checklist_id>/export/',
        views.export_checklist_view, name='ps-checklist-export'),
    path('checklists/<int:checklist_id>/edit/',
        views.edit_checklist_view, name='ps-checklist-edit'),
    # dialog for AJAX-based delete of single checklist
    path('checklists/<int:checklist_id>/delete/',
        views.delete_checklist_view, name='ps-checklist-delete'),

    # Find People
    path('people/', views.find_people_view, name='ps-find-people'),
    re_path(r'^people/(?P<username>[A-Za-z0-9_@+-.]+)/$',
        views.find_people_profile_view, name='ps-find-people-profile'),

    # Your Profile page
    path('profile/', views.your_profile_view, name='ps-your-profile'),

    # Staff-Only area urls
    path('staff/images', views.screen_images, name='ps-screen-images'),

    # AJAX urls
    path('api/edit-profile', views.ajax_profile_edit,
        name='ps-ajax-profile-edit'),
    path('api/image-upload', views.ajax_image_upload,
        name='ps-ajax-image-upload'),
    path('api/image-reject/<int:image_id>', views.ajax_image_reject,
        name='ps-ajax-image-reject'),
    path('api/sightings/', views.ajax_sightings, name='ps-ajax-sightings'),
    path('api/people-suggestions/', views.ajax_people_suggestions,
        name='ps-ajax-people-suggestions'),
    path('api/restrictions/', views.ajax_restrictions,
        name='ps-ajax-restrictions'),
]