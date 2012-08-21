require([
    'util/activate_image_gallery',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/sidebar',
    'util/activate_video_links',
    'simplekey/glossarize'
], function(activate_image_gallery, Shadowbox, shadowbox_init, sidebar,
            activate_video_links, glossarize) {
    sidebar.setup();
    $(document).ready(function() {
        glossarize($('.key-char, .exceptions'));
    });
});
