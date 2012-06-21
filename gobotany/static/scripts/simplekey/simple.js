require([
    'util/activate_image_gallery',
    'util/activate_search_suggest',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/sidebar',
    'util/activate_video_links'
]);

require([
    'simplekey/glossarize'
], function(glossarize) {
    $(document).ready(function() {
        glossarize($('.key-char, .exceptions'));
    });
});
