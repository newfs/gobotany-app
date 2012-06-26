define([
    'bridge/jquery',
    'gobotany/sk/family',
    'util/sidebar',
    'util/activate_search_suggest',
    'util/shadowbox_init',
    'simplekey/glossarize'
], function($, family, sidebar, activate_search_suggest, shadowbox_init,
    glossarize) {

    var module_function = function(args) {
        $(document).ready(function() {
            glossarize($('.description'));
            sidebar.setup();
            family.init(args.family_slug);
        });
    };

    return module_function;
});
