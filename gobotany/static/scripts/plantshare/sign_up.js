define([
    'bridge/jquery'
], function ($) {

    $(document).ready(function () {
        // Set tab index attributes on the form fields so the user can
        // press tab on them through all of the fields.
        
        $('#id_username').attr('tabindex', 10);
        $('#id_email').attr('tabindex', 20);
        $('#id_password1').attr('tabindex', 30);
        $('#id_password2').attr('tabindex', 40);
        $('#sign_up_button').attr('tabindex', 50);

        // Set the initial focus to the first input box.
        $('#main form input[type="text"]').eq(0).focus();
    });
});


