"""
Customized URLConf for our customized django-registration backend.
NOTE: This can be tweaked in the future if we want to change the workflow
a little.
"""

from django.contrib.auth.views import (LoginView, LogoutView,
    PasswordChangeView, PasswordChangeDoneView, PasswordResetView,
    PasswordResetDoneView, PasswordResetConfirmView,
    PasswordResetCompleteView)
from django.urls import path, re_path
from django.views.generic.base import TemplateView

from django_registration.backends.activation.views import (ActivationView,
    RegistrationView)

from gobotany.plantshare.views import (change_email,
    change_email_confirmation_sent, confirm_email)
from .forms import RegistrationFormWithHiddenField

###
# These URLs are all under: /plantshare/accounts/
###

urlpatterns = [
    path('activate/complete/', TemplateView.as_view(
            template_name='registration/activation_complete.html'),
        name='django_registration_activation_complete'),
    # Activation keys get matched by a string instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key should still get to the
    # view; that way it can return a sensible "invalid key" message instead
    # of a confusing 404.
    path('activate/<str:activation_key>/', ActivationView.as_view(
            template_name='registration/activation_failed.html'),
        name='django_registration_activate'),
    path('register/', RegistrationView.as_view(
            form_class=RegistrationFormWithHiddenField,
            email_subject_template='registration/activation_email_subject.txt',
            email_body_template='registration/activation_email.txt',
            template_name='registration/registration_form.html'),
        name='django_registration_register'),
    path('register/complete/', TemplateView.as_view(
            template_name='registration/registration_complete.html'),
        name='django_registration_complete'),
    path('register/closed/', TemplateView.as_view(
            template_name='registration/registration_closed.html'),
        name='django_registration_disallowed'),

    ###
    # Change Password and Forgot Password (reset)
    #
    # Use names from django.auth.urls.py to avoid a NoMatch error as seen with
    # password_reset_done (http://stackoverflow.com/questions/20307473).
    #
    # Change Password
    #
    # 1. Change Password form (also appears on Your Profile page)
    path('password/change/', PasswordChangeView.as_view(
            template_name='registration/change_password.html'),
        name='password_change'),
    # 2. Done changing password (confirmation page)
    path('password/change/done/', PasswordChangeDoneView.as_view(
            template_name='registration/change_password_done.html'),
        name='password_change_done'),

    # Forgot Password (reset password)
    #
    # 1. Forgot Password form
    path('password/reset/', PasswordResetView.as_view(
            template_name='registration/forgot_password.html'),
        name='password_reset'),
    # 2. Reset password email sent (confirmation page)
    path('password/reset/done/', PasswordResetDoneView.as_view(
            template_name='registration/reset_password_email_sent.html'),
        name='password_reset_done'),
    # 3. Link sent in reset password email: redirects to
    # Choose New Password form (.../set-password/)
    re_path(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/'
        'r(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(
            template_name='registration/choose_new_password.html'),
        name='password_reset_confirm'),
    # 4. Done choosing new password (confirmation page)
    path('password/reset/complete/', PasswordResetCompleteView.as_view(
            template_name='registration/change_password_done.html'),
        name='password_reset_complete'),

    # Change Email Address
    #
    path('email/change/', change_email, name='ps-change-email'),
    path('email/change/confirmation-sent/', change_email_confirmation_sent,
        name='ps-change-email-confirmation-sent'),
    path('email/confirm/<str:key>/', confirm_email, name='ps-confirm-email'),

    # Log In, Log Out
    path('login/', LoginView.as_view(
        template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(
        template_name='registration/logout.html'), name='logout'),
]