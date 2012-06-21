/* Code for cross-fading a set of images. */
// JQuery is included in dependencies here for 
// documentation purposes but AMD support is 
// minimal at this point so we're still using 
// the global object
define([
    'bridge/jquery'
    ], 
    function($) {
        // This is still global while we transition to AMD
        fade_next_banner_image = function() {
            var FADE_DURATION = 2 * 1000;
            var BANNER_IMAGE_CSS = '#banner > img';

            // Simultaneously fade out the currently visible image
            // and fade in the next image.
            var images = $(BANNER_IMAGE_CSS);
            var i, next_image;
            var visible_image = $(images[0]);
            for (i = 0; i < images.length; i++) {
                if ($(images[i]).is(':visible')) {
                    visible_image = $(images[i]);
                    break;
                }
            }
            if (i < (images.length - 1)) {
                next_image = $(images[i + 1]);
            }
            else {
                next_image = $(images[0]);
            }
            visible_image.fadeOut(FADE_DURATION);
            next_image.fadeIn(FADE_DURATION);
        };
    return fade_next_banner_image;
    }
);
