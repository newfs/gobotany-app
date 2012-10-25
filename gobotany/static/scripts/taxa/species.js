define([
    'bridge/jquery',
    // Basic resources
    'util/shadowbox_init',

    // Scrolling
    'util/activate_smooth_div_scroll',

    'taxa/SpeciesPageHelper'
], function($, shadowbox_init, activate_scroll, SpeciesPageHelper) {

    $(document).ready(function() {
        var helper = SpeciesPageHelper();
        helper.setup();
    });
});
