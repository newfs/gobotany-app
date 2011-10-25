define([
], {
    /* Since the HTML template is what knows the pile_slug, we provide
     * it with a function it can invoke that takes the pile_slug as an
     * argument.
     */
    startup: function(pile_slug) {

        require([
            'simplekey/results_overlay'
        ]);

        require([
            'dojo',
            'order!jquery.tools.min',  // needed by jscrollpane
            'order!jquery.jscrollpane.min',  // sk/results.js
            'underscore-min',  // filters.js, etc
            'global'  // sk/results.js, etc
        ], function() {
            dojo.require('gobotany.sk.results');
            dojo.addOnLoad(function() {
                helper = gobotany.sk.results.ResultsHelper(pile_slug);
                helper.setup();
            });
        });

        /* Hook up our gallery applications. */

        require([
            'activate_image_gallery',
            'activate_search_suggest',
            'shadowbox'
        ], function() {
            Shadowbox.init({
                onOpen: function() {
                    // Move the Shadowbox close link.
                    var tb = document.getElementById('sb-wrapper');
                    if (tb) {
                        var snc = document.getElementById('sb-nav-close');
                        tb.appendChild(snc);
                    }
                }
            });
        });
    }
});
