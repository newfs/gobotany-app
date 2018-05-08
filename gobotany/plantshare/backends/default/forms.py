from registration.forms import RegistrationForm
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

class RegistrationFormWithCaptcha(RegistrationForm):
    captcha = ReCaptchaField(widget=ReCaptchaWidget())