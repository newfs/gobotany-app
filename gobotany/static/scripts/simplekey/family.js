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
        dojo.require('gobotany.sk.family');
        dojo.addOnLoad(function() {
            gobotany.sk.family.init(args.family_slug);
        });
    });

});
