"""
Customized URLConf for our customized django-registration backend.
NOTE: This can be tweaked in the future if we want to change the workflow
a little.
"""

from django.conf.urls import url
from django.contrib.auth.views import (LoginView, LogoutView,
    PasswordChangeView, PasswordChangeDoneView, PasswordResetView,
    PasswordResetDoneView, PasswordResetConfirmView,
    PasswordResetCompleteView)
from django.views.generic.base import TemplateView

from django_registration.backends.activation.views import (ActivationView,
    RegistrationView)

from gobotany.plantshare.views import (change_email,
    change_email_confirmation_sent, confirm_email)
from .forms import RegistrationFormWithHiddenField

urlpatterns = [
    url(r'^activate/complete/$',
        TemplateView.as_view(
            template_name='registration/activation_complete.html'),
        name='registration_activation_complete'),
    # Activation keys get matched by \w+ instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key should still get to the
    # view; that way it can return a sensible "invalid key" message instead
    # of a confusing 404.
    url(r'^activate/(?P<activation_key>\w+)/$',
        ActivationView.as_view(),
        name='registration_activate'),
    url(r'^register/$',
        RegistrationView.as_view(form_class=RegistrationFormWithHiddenField),
        name='registration_register'),
    url(r'^register/complete/$',
        TemplateView.as_view(
            template_name='registration/registration_complete.html'),
        name='registration_complete'),
    url(r'^register/closed/$',
        TemplateView.as_view(
            template_name='registration/registration_closed.html'),
        name='registration_disallowed'),

    ###
    # Change Password and Forgot Password (reset)
    #
    # Use names from django.auth.urls.py to avoid a NoMatch error as seen with
    # password_reset_done (http://stackoverflow.com/questions/20307473).
    #
    # Change Password
    #
    # 1. Change Password form (also appears on Your Profile page)
    #url(r'^password/change/$', password_change,
    #    {'template_name': 'registration/change_password.html'},
    #    name='password_change'),
    url(r'^password/change/$',
        PasswordChangeView.as_view(
            template_name='registration/change_password.html'),
        name='password_change'),
    # 2. Done changing password (confirmation page)
    url(r'^password/change/done/$',
        PasswordChangeDoneView.as_view(
            template_name='registration/change_password_done.html'),
        name='password_change_done'),

    # Forgot Password (reset password)
    #
    # 1. Forgot Password form
    url(r'^password/reset/$',
        PasswordResetView.as_view(
            template_name='registration/forgot_password.html'),
        name='password_reset'),
    # 2. Reset password email sent (confirmation page)
    url(r'^password/reset/done/$',
        PasswordResetDoneView.as_view(
            template_name='registration/reset_password_email_sent.html'),
        name='password_reset_done'),
    # 3. Link sent in reset password email: redirects to
    # Choose New Password form (.../set-password/)
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(
            template_name='registration/choose_new_password.html'),
        name='password_reset_confirm'),
    # 4. Done choosing new password (confirmation page)
    url(r'^password/reset/complete/$',
        PasswordResetCompleteView.as_view(
            template_name='registration/change_password_done.html'),
        name='password_reset_complete'),

    # Change Email Address
    #
    url(r'^email/change/$', change_email,
        name='ps-change-email'),
    url(r'^email/change/confirmation-sent/$', change_email_confirmation_sent,
        name='ps-change-email-confirmation-sent'),
    url(r'^email/confirm/(?P<key>\w+)/$', confirm_email,
        name='ps-confirm-email'),

    # Log In, Log Out
    url(r'^login/$', LoginView.as_view(
            template_name='registration/login.html'),
        name='login'),
    url(r'^logout/$', LogoutView.as_view(
            template_name='registration/logout.html'),
        name='logout'),
]
