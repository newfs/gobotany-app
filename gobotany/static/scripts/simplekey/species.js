require([
    'activate_search_suggest',
    'shadowbox'
], function() {

    Shadowbox.init({
        onOpen: function() {
            // Move the Shadowbox close link.
            var tb = document.getElementById('sb-wrapper');
            if (tb) tb.appendChild(document.getElementById('sb-nav-close'));
        }
    });
});

require([
    'dojo_config',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js',
    'global'  // for global_setSidebarHeight
], function() {

    dojo.require('gobotany.sk.species');
    dojo.addOnLoad(function() {
        var helper = gobotany.sk.species.SpeciesPageHelper();
        helper.setup();
    });    

});

require([
    'activate_smooth_div_scroll'
]);
