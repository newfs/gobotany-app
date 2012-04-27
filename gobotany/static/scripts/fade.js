/* Code for cross-fading a set of images. */
// JQuery is included in dependencies here for 
// documentation purposes but AMD support is 
// minimal at this point so we're still using 
// the global object
define([
    'jquery.tools.min'
    ], 
    function(jquery) {
        // This is still global while we transition to AMD
        fade_next_banner_image = function() {
            var FADE_DURATION = 2 * 1000;
            var BANNER_IMAGE_CSS = '#banner > img';
            // Successively fade in each hidden image.
            var fade = $(BANNER_IMAGE_CSS + ':hidden:first');
            if (fade.length > 0) {
                fade.fadeIn(FADE_DURATION);
            } else {
                // Start over: hide all but first and last again, then fade
                // the last out to the first.
                var images = $(BANNER_IMAGE_CSS);
                $(images).each(function(index) {
                    if ((index !== 0) && (index !== images.length - 1)) {
                        $(this).css('display', 'none');
                    }
                });
                fade = $(BANNER_IMAGE_CSS + ':visible:last');
                fade.fadeOut(FADE_DURATION);
            }
        };
    return fade_next_banner_image;
    }
);
