/*
 * Activate an element with id="species-images" with the Smooth Div Scroll
 * component.
 */

require([
    'jquery.tools.min',
], function() {
    require([
        'jquery-ui-1.8.16.custom.min',
    ], function() {
        require([
            'jquery.smoothDivScroll-1.1-mod', /* un-minified, with bugfix by
                                                 Go Botany */
        ], function() {
            $(document).ready(function() {
                $('#species-images').smoothDivScroll({
                    autoScroll: 'onstart', 
                    autoScrollDirection: 'backandforth', 
                    autoScrollStep: 1, 
                    autoScrollInterval: 75,
                    visibleHotSpots: 'always'
                });
            });
        });
    });
});
