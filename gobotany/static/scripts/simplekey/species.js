define([

    // Basic resources

    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init',

    // Page components

    'sidebar',
    'simplekey/glossarize',

    // Scrolling

    'activate_smooth_div_scroll'

], function(x, x, x, x, _glossarize, x) {
    glossarize = _glossarize;
    dojo.require('gobotany.sk.species');
    dojo.addOnLoad(function() {
        var helper = gobotany.sk.species.SpeciesPageHelper();
        helper.setup();
    });
});
