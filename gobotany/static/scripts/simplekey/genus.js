define([
    'bridge/jquery',
    'simplekey/glossarize'
], function($, glossarize) {
    
    var module_function = function(args) {
        $(document).ready(function() {
            glossarize($('.description'));
        });

        require([
            'util/activate_search_suggest',
            'bridge/shadowbox',
            'util/shadowbox_init'
        ]);

        require([
            'util/sidebar'
        ], function() {
            dojo.require('gobotany.sk.genus');
            dojo.addOnLoad(function() {
                gobotany.sk.genus.init(args.genus_slug);
            });
        });
    };

    return module_function;
});

