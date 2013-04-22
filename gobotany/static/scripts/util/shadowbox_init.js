/* Make a few global customizations to Shadowbox initialization. */

define([
    'bridge/jquery', 
    'bridge/shadowbox'
], function ($, Shadowbox) {

    // Animate and position the close button.
    shadowbox_move_close_button = function () {
        var cb = document.getElementById('sb-nav-close');
        var tb = document.getElementById('sb-wrapper');
        if (tb) {
            tb.appendChild(cb);
        }
    };

    shadowbox_on_open = function () {
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

    shadowbox_on_close = function () {
        // Hide any tooltips activated from the lightbox.
        $('.gb-tooltip.dark').hide();
    };

    $(document).ready(function () {
        Shadowbox.init({
            onClose: shadowbox_on_close,
            onOpen: shadowbox_on_open,
            overlayOpacity: 0.8
        });
    });

    /* Return Shadowbox as a convenience, so users do not have to import
       both Shadowbox and shadowbox_init themselves. */

    return Shadowbox;
});
