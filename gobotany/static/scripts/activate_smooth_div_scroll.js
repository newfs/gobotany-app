/*
 * Activate an element with id="species-images" with the Smooth Div Scroll
 * component.
 */

require([
    'jquery.tools.min'
], function() {
    require([
        'jquery-ui-1.8.16.custom.min'
    ], function() {
        require([
            'lib/jquery.smoothDivScroll-1.2' /* un-minified, with bugfix by
                                                Go Botany */
        ], function() {
            $(document).ready(function() {

               // Even though we leave mousewheeling turned off, the
               // smoothDivScroll will still try to register an event
               // handler, so we create a fake widget to avoid an error.

               $.widget('fake.mousewheel', {});

               // Activate!

               $('#species-images').smoothDivScroll({
                    autoScroll: 'onstart', 
                    autoScrollDirection: 'backandforth', 
                    autoScrollStep: 1, 
                    autoScrollInterval: 75,
                    visibleHotSpotBackgrounds: 'always'
                });
            });
        });
    });
});
