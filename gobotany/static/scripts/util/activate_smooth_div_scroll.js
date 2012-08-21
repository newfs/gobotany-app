/*
 * Activate an element with id="species-images" with the Smooth Div Scroll
 * component.
 */

require([
    'bridge/jquery',
    'bridge/jquery-ui',
    'bridge/jquery.easing',
    'bridge/jquery.smoothdivscroll'
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
    
        // Manually fire the window.load event in order to start
        // autoscrolling. (It used to work without this before some code
        // reorganization, so perhaps it can be removed at some point.)
        $(window).load();
    });
});
