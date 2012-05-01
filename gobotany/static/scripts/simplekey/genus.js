define([
    'args',
    'jquery',
    'simplekey/glossarize'
], function(args, x, glossarize) {

    $(document).ready(function() {
        glossarize($('.description'));
    });

    require([
        'activate_search_suggest',
        'shadowbox',
        'shadowbox_init'
    ]);

    require([
        'sidebar'
    ], function() {
        dojo.require('gobotany.sk.genus');
        dojo.addOnLoad(function() {
            gobotany.sk.genus.init(args.genus_slug);
        });
    });

});

