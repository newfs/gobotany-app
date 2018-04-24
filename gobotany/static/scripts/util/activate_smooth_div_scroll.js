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
    'bridge/jquery.smoothdivscroll',
    'bridge/shadowbox',
    'util/PhotoHelper'
], function($, ui, easing, kinetic, mousewheel, smoothDivScroll,
        Shadowbox, PhotoHelper) {
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
            options.mousewheelScrolling = false;
        }
        else {
            options.visibleHotSpotBackgrounds = 'always';
        }

        options.setupComplete = function () {
            // Set up necessary events for image links in the gallery.
            // This has to be done after setup has completed in order
            // for the event handlers to register properly.
            var photo_helper = PhotoHelper();
            Shadowbox.setup('.img-gallery .images a', {
                onOpen: photo_helper.prepare_to_enlarge,
                onChange: photo_helper.prepare_to_enlarge,
                onFinish: photo_helper.process_credit
            });
        };

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
