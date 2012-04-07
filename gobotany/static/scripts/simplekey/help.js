require([
    'activate_search_suggest',
    'activate_video_links'
]);

require([
    'order!dojo_config',
    'order!/static/js/dojo/dojo.js'
], function() {
    require([
        '/static/js/layers/sk.js'
    ]);
});

require([
    'shadowbox',
    'shadowbox_close',
    'sidebar'
]);

