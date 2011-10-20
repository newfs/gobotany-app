define([
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
