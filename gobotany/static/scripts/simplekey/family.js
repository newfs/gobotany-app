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
        ], function(sidebar) {
            sidebar.setup();
            dojo.require('gobotany.sk.family');
            dojo.addOnLoad(function() {
                gobotany.sk.family.init(args.family_slug);
            });
        });
    };

    return module_function;
});
