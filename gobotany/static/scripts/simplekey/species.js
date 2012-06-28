define([
    'bridge/jquery',
    // Basic resources
    'util/activate_search_suggest',
    'util/shadowbox_init',
    
    // Scrolling
    'util/activate_smooth_div_scroll',
    
    'gobotany/sk/species'
], function($, search_suggest, shadowbox_init, activate_scroll,
    SpeciesPageHelper) {

    $(document).ready(function() {
        var helper = SpeciesPageHelper();
        helper.setup();
    });
});
