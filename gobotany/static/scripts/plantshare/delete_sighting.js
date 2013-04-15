define([
    'bridge/jquery'
], function ($) {
    $(document).ready(function () {
        // Set up Cancel button.
        $('.cancel-btn').click(function () {
            window.parent.Shadowbox.close();
        });
    });
});
