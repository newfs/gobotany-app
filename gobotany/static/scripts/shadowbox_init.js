/* Make a few global customizations to Shadowbox initialization. */

define([
    'bridge/jquery', 
    'shadowbox'
], function($) {

    // Animate and position the close button.
    shadowbox_move_close_button = function() {
        var cb = document.getElementById('sb-nav-close');
        var tb = document.getElementById('sb-wrapper');
        if (tb) {
            tb.appendChild(cb);
        }
    };

    shadowbox_on_open = function() {
        // Work around a bug when using lightboxes on iOS:
        // On iOS versions older than 5, lightboxes can appear off the
        // screen if the page is scrolled down, so scroll to the top.
        if (navigator.userAgent.match(/(iPad|iPod|iPhone)/)) {
            if (navigator.userAgent.match(/(OS 3_|OS 4_)/)) {
                window.scrollTo(0, 0);
            }
        }

        shadowbox_move_close_button();
    };

    $(document).ready(function() {
        Shadowbox.init({
            onOpen: shadowbox_on_open
        });
    });
});
