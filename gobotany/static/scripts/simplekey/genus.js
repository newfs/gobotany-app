define([
    'args'
], function(args) {

    require([
        'activate_search_suggest'
    ]);

    require([
        'dojo',
        'dojo_config',
        '/static/js/dojo/dojo.js',
        '/static/js/layers/sk.js',
        'sidebar'
    ], function() {

        dojo.require('gobotany.sk.genus');
        dojo.addOnLoad(function() {
            gobotany.sk.genus.init(args.genus_slug);
        });

    });

});

