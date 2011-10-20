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
    'dojo',
    'order!jquery.tools.min',
    'order!jquery.jscrollpane.min',
    'underscore-min',
    'global',  // for global_setSidebarHeight
    'simplekey/results_overlay'
], function() {

    /* Since the HTML template is what knows the pile_slug, we provide
     * it with a function it can invoke that takes the pile_slug as an
     * argument.
     */
    return function(pile_slug) {
        dojo.require('gobotany.sk.results');
        dojo.addOnLoad(function() {
            helper = gobotany.sk.results.ResultsHelper(pile_slug);
            helper.setup();
        });
    };
});
