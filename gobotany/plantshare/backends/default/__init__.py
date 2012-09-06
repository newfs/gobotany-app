from registration.backends.default import DefaultBackend
from captcha.forms import RegistrationFormCaptcha


class PlantShareDefaultBackend(DefaultBackend):
    """
    Simple custom extension to the default backend, allow captcha integration.
    """
    def get_form_class(self, request):
        """
        Return reCaptcha-enabled registration form.
        
        """
        return RegistrationFormCaptcha
