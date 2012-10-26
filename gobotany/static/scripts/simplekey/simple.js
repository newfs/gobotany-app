require([
    'util/activate_image_gallery',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/sidebar',
    'util/activate_video_links',
    'util/glossarizer'
], function(activate_image_gallery, Shadowbox, shadowbox_init, sidebar,
            activate_video_links, glossarizer) {
    sidebar.setup();
    $(document).ready(function() {
        glossarizer.glossarize($('.key-char, .exceptions'));
    });
});
