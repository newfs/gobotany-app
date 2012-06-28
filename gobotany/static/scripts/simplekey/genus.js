define([
    'bridge/jquery',
    'gobotany/sk/genus',
    'util/sidebar',
    'util/activate_search_suggest',
    'util/shadowbox_init',
    'simplekey/glossarize'
], function($, genus, sidebar, activate_search_suggest, shadowbox_init,
    glossarize) {
    
    var module_function = function(args) {
        $(document).ready(function() {
            glossarize($('.description'));
            sidebar.setup();
            genus.init(args.genus_slug);
        });
    };

    return module_function;
});

