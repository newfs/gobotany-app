require([
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init'
]);

require([
    'sidebar',
    'simplekey/glossarize'
], function(x, _glossarize) {
    glossarize = _glossarize;
    dojo.require('gobotany.sk.species');
    dojo.addOnLoad(function() {
        var helper = gobotany.sk.species.SpeciesPageHelper();
        helper.setup();
    });
});

require([
    'activate_smooth_div_scroll'
]);
