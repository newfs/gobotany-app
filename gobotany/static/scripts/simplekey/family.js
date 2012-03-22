define([
    'args'
], function(args) {

    require([
        'activate_search_suggest',
        'shadowbox',
        'shadowbox_close'
    ]);

    require([
        'order!dojo_config',
        'order!/static/js/dojo/dojo.js',
        'sidebar'
    ], function() {
        require([
            '/static/js/layers/sk.js'
        ], function() {
            dojo.require('gobotany.sk.family');
            dojo.addOnLoad(function() {
                gobotany.sk.family.init(args.family_slug);
            });
        });
    });

});
