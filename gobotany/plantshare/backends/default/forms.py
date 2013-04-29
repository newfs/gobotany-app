from captcha.fields import ReCaptchaField
from registration.forms import RegistrationForm


class RegistrationFormWithCaptcha(RegistrationForm):
    captcha = ReCaptchaField(attrs={'theme': 'clean'})
