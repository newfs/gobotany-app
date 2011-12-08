define(['jquery.tools.min'], function() {

    // Animate and position the Shadowbox close button.
    shadowbox_close_move_button = function() {
        var cb = document.getElementById('sb-nav-close');
        var tb = document.getElementById('sb-wrapper');
        if (tb) {
            tb.appendChild(cb);
        }
    };

    $(document).ready(function() {
        Shadowbox.init({
            onOpen: shadowbox_close_move_button
        });
    });
});
