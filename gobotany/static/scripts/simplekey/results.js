 define([
    'args'
], function(args) {

    require([
        'simplekey/results_overlay',
        'simplekey/results_photo_menu'
    ]);

    require([
        'dojo',
        'order!jquery.tools.min',  // needed by jscrollpane
        'order!jquery.jscrollpane.min',  // sk/results.js
        'underscore-min',  // filters.js, etc
        'sidebar',
        'simplekey/resources'  // now used in filters.js
    ], function() {
        dojo.require('gobotany.sk.results');
        dojo.addOnLoad(function() {
            helper = gobotany.sk.results.ResultsHelper(args.pile_slug);
            helper.setup();
        });
    });

    /* Hook up our gallery applications. */

    require([
        'activate_image_gallery',
        'activate_search_suggest',
        'shadowbox',
        'shadowbox_close'
    ]);
});
