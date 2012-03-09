/*
 * Activate an element with id="species-images" with the Smooth Div Scroll
 * component.
 */

require([
    'jquery.tools.min',
    'smoothDivScroll'
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
