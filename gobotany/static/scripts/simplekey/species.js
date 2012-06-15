define([

    // Basic resources

    'util/activate_search_suggest',
    'bridge/shadowbox',
    'util/shadowbox_init',

    // Page components

    'util/sidebar',
    'simplekey/glossarize',

    // Scrolling

    'util/activate_smooth_div_scroll'

], function(search_suggest, ShadowBox, shadowbox_init, sidebar, _glossarize, 
        activate_scroll) {
    sidebar.setup();
    glossarize = _glossarize;
    dojo.require('gobotany.sk.species');
    dojo.addOnLoad(function() {
        var helper = gobotany.sk.species.SpeciesPageHelper();
        helper.setup();
    });
});
