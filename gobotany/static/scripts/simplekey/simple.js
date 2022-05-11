require([
    'util/activate_image_gallery',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/activate_video_links',
    'util/glossarizer'
], function(activate_image_gallery, Shadowbox, shadowbox_init,
            activate_video_links, glossarizer) {
    $(document).ready(function () {
        glossarizer.glossarize($('.key-char + p, .exceptions + p'));

        // Allow activating the image gallery dialog using the keyboard.
        $('.img-container').on('keydown', function (event) {
            var keyCode = event.which;
            if (keyCode == 32) {   // Space key
                // Prevent page scrolling on pressing Space.
                event.preventDefault();
            }
        });
        $('.img-container').on('keyup', function (event) {
            var keyCode = event.which;
            if (keyCode == 13 || keyCode == 32) {   // Return, Space keys
                $(event.target).trigger('click');
            }
        });
    });
});
