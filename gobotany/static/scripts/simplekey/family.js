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

        dojo.require('gobotany.sk.family');
        dojo.addOnLoad(function() {
            gobotany.sk.family.init(args.family_slug);
        });

    });

});
