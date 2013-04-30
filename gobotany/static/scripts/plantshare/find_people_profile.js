define([
    'bridge/jquery'
], function ($) {
    $(document).ready(function () {

        // Set up Close button.
        $('.close').click(function () {
            window.parent.Shadowbox.close();
        });
    });
});
