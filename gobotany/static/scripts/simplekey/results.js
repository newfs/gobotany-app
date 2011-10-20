require([
    'activate_image_gallery',
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

define([
    'simplekey/results_overlay',  // we activate this early
    'dojo_config',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js',
    'jquery.tools.min',
    'jquery.jscrollpane.min',
    'underscore-min',
    'global'  // for global_setSidebarHeight
], {
    go: function(pile_slug) {
        dojo.require('gobotany.sk.results');
        dojo.addOnLoad(function() {
            helper = gobotany.sk.results.ResultsHelper(pile_slug);
            helper.setup();
        });
    }
});
