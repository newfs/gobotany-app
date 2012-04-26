require([
    'activate_image_gallery',
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init',
    'sidebar',
    'activate_video_links'
]);

require([
    'simplekey/glossarize'
], function(glossarize) {
    glossarize($('.key-char, .exceptions'));
});
