define([
    'bridge/jquery'
], function ($) {

    $(document).ready(function () {
        // Set tab index attributes on the form fields so the user can
        // press tab on them through all of the fields (including the
        // captcha field) right up to the Sign Me Up button.
        
        $('#id_username').attr('tabindex', 10);
        $('#id_email').attr('tabindex', 20);
        $('#id_password1').attr('tabindex', 30);
        $('#id_password2').attr('tabindex', 40);
        $('#recaptcha_response_field').attr('tabindex', 50);
        $('#sign_up_button').attr('tabindex', 60);

        // Include the little extra recaptcha buttons in the tab order
        // for completeness's sake, but put them at the end so they no
        // longer interfere with tabbing from the recaptcha text field
        // to the Sign Me Up button.
        $('#recaptcha_reload').attr('tabindex', 70);
        $('#recaptcha_switch_audio').attr('tabindex', 80);
        $('#recaptcha_whatsthis').attr('tabindex', 90);

        // Set the initial focus to the first input box.
        $('#main form input[type="text"]').eq(0).focus();
    });
});


