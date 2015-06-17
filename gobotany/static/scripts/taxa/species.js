define([
    'bridge/jquery',
    // Basic resources
    'util/shadowbox_init',

    // Scrolling
    'util/activate_smooth_div_scroll',

    'taxa/SpeciesPageHelper',
    'util/image_popup'
], function($, shadowbox_init, activate_scroll, SpeciesPageHelper,
    image_popup) {

    $(document).ready(function() {
        var helper = SpeciesPageHelper();
        helper.setup();

        // Clicking on D. Key figure links pops up a larger image.
        image_popup.init();
        image_popup.pop_up_links('.figure-link');
    });
});
