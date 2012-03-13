define([
    'args'
], function(args) {

    require([
        'simplekey/results_overlay',
        'simplekey/results_photo_menu'
    ]);

    require([
        'order!dojo_config',
        'order!/static/js/dojo/dojo.js',
        'underscore-min',  // filters.js, etc
        'sidebar',
        'simplekey/resources',  // now used in filters.js
        'jscrollpane',  // sk/results.js
        'shadowbox'
    ], function() {
        require([
            '/static/js/layers/sk.js'
        ], function() {
            dojo.require('gobotany.sk.results');
            dojo.addOnLoad(function() {
                helper = gobotany.sk.results.ResultsHelper(args.pile_slug);
            });
        });
    });

    /* Hook up our gallery applications. */

    require([
        'activate_image_gallery',
        'activate_search_suggest',
        'shadowbox_close'
    ]);
});
