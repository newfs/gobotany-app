define([
    'bridge/jquery',
    'bridge/jquery.cookie'
], function ($, x1) {

    $(document).ready(function () {

        // Set a cookie indicating that the user completed the registration
        // process. This will be used to omit the "Sign Up" call to action
        // when the user is signed out.
        $.cookie('registration_complete', 'True',
                 {expires: (10 * 365), path: '/'});
    });
});

