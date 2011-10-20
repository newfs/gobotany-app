/*
 * Activate a element with id="species-images" with the Smooth Div Scroll
 * component.
 */

require([
    'jquery.tools.min',
    'jquery-ui-1.8.16.custom.min',
    'jquery.smoothDivScroll-1.1-min'
], function() {

    /* So far the Smooth Div Scroll plugin is only working in
       Firefox, not in WebKit-based browsers. Smooth Div Scroll
       is said to require jQuery 1.5.2. However, no matter whether using
       jQuery versions 1.4.2, 1.5.2 or 1.6.x, Smooth Div Scroll usually
       doesn't work on our page in in WebKit. But, it does work fine on
       the Smooth Div Scroll demo page, so there is probably a way to get
       it working. */
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
