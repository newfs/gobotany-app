/*
 * Activate an element with id="species-images" with the Smooth Div Scroll
 * component.
 */

require([
    'bridge/jquery',
    'bridge/jquery-ui',
    'bridge/jquery.easing',
], function($, ui, easing) {
    require([
        'lib/jquery.smoothDivScroll-1.2-mod' // un-minified, with bugfix
                                             // by Go Botany
    ], function() {
        $(document).ready(function() {

           // Even though we leave mousewheeling turned off, the
           // smoothDivScroll will still try to register an event
           // handler, so we create a fake widget to avoid an error.

           $.widget('fake.mousewheel', {});

           // Activate!
           
           $('#species-images').smoothDivScroll({
               autoScrollingMode: 'onstart', 
               autoScrollingDirection: 'backandforth', 
               autoScrollingStep: 1, 
               autoScrollingInterval: 75,
               visibleHotSpotBackgrounds: 'always'
           });
        });
    });
});
