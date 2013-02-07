/*
 * Activate an element with id="species-images" with the Smooth Div Scroll
 * component.
 */

require([
    'bridge/jquery',
    'bridge/jquery-ui',
    'bridge/jquery.easing',
    'bridge/jquery.kinetic',
    'bridge/jquery.mousewheel',
    'bridge/jquery.smoothdivscroll'
], function($, ui, easing, kinetic, mousewheel, smoothDivScroll) {
    $(document).ready(function () {

        var $images = $('#species-images');

        var is_touch = navigator.userAgent.match(
                       /(iPad|iPod|iPhone|Android)/) ? true : false;

        var options = {
            autoScrollingMode: 'onStart',
            autoScrollingMode: 'onStart', 
            autoScrollingDirection: 'backAndForth', 
            autoScrollingStep: 1, 
            autoScrollingInterval: 75
        };

        // Add options for either mouse or touch.
        if (is_touch) {
            options.hotSpotScrolling = false;
            options.touchScrolling = true;
            options.mousewheelScrolling = false;
        }
        else {
            options.visibleHotSpotBackgrounds = 'always';
        }

        // Activate.
        $images.smoothDivScroll(options);
    
        // Stop autoscrolling upon viewing an image.
        $images.bind('click', function () {
            $images.smoothDivScroll('stopAutoScrolling');
        });
        
        // Fire the window.load event in order to start autoscrolling.
        // (It used to work without this in an older version, so perhaps
        // this can be removed at some point.)
        $(window).load();
    });
});
