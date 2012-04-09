require([
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init'
]);

require([
    'dojo_config',
    'sidebar',
    'simplekey/resources'
], function() {
    require([
        '/static/js/dojo/dojo.js'
    ], function() {
        require([
            '/static/js/layers/sk.js'
        ], function() {
            dojo.require('gobotany.sk.species');
            dojo.addOnLoad(function() {
                var helper = gobotany.sk.species.SpeciesPageHelper();
                helper.setup();
            });
        });
    });
});

require([
    'activate_smooth_div_scroll'
]);
