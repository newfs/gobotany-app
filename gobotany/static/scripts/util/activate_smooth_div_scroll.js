/*
 * Activate an element with id="species-images" with the Smooth Div Scroll
 * component.
 */

require([
    'bridge/jquery',
    'bridge/jquery-ui',
    'bridge/jquery.easing',
    'bridge/jquery.smoothDivScroll'
], function($, ui, easing, smoothDivScroll) {
    $(document).ready(function() {

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
