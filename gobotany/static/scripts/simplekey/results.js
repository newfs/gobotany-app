define([
    'args',
    'simplekey/App3'
], function(args, App3) {

    App3.taxa = Ember.Object.create({
        len: 'Loading'  // placeholder until we have an integer to display
    });

    App3.image_types = Ember.ArrayProxy.create({
        content: []
    });

    require([
        'simplekey/results_overlay',
        'simplekey/results_photo_menu'
    ]);

    require([
        'jquery.tools.min',
        'order!jscrollpane'   // sk/results.js
    ], function() {
        require([
            'order!dojo_config',
            'order!/static/js/dojo/dojo.js',
            'order!/static/js/layers/nls/sk_en-us.js',
            'order!/static/js/layers/sk.js'
        ], function() {
            require([
                'order!/static/gobotany/filters.js',
                'order!/static/gobotany/utils.js',
                'order!/static/gobotany/sk/glossary.js',
                'order!/static/gobotany/sk/photo.js',
                'order!/static/gobotany/sk/results.js',
                'order!/static/gobotany/sk/SpeciesSectionHelper.js',
                'order!/static/gobotany/sk/working_area.js',
                'order!/static/gobotany/sk/SearchSuggest.js'
            ], function() {
                require([
                    'order!simplekey/resources',   // now used in filters.js
                    'order!activate_search_suggest',
                    'order!activate_image_gallery',
                    'underscore-min',  // filters.js, etc
                    'sidebar',
                    'shadowbox',
                    'shadowbox_init'
                ], function() {
                    dojo.require('gobotany.sk.results');
                    dojo.addOnLoad(function() {
                        helper = gobotany.sk.results.ResultsHelper(args.pile_slug);
                    });
                });
            });
        });
    });
});
