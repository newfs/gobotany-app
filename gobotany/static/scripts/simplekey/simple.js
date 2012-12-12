require([
    'util/activate_image_gallery',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/activate_video_links',
    'util/glossarizer'
], function(activate_image_gallery, Shadowbox, shadowbox_init,
            activate_video_links, glossarizer) {
    $(document).ready(function() {
        glossarizer.glossarize($('.key-char, .exceptions'));
    });
});
