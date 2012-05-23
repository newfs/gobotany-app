define([
    'args',
    'bridge/jquery',
    'simplekey/glossarize'
], function(args, $, glossarize) {

    $(document).ready(function() {
        glossarize($('.description'));
    });

    require([
        'activate_search_suggest',
        'bridge/shadowbox',
        'util/shadowbox_init'
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

