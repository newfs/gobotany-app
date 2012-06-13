define([

    // Basic resources

    'util/activate_search_suggest',

    // Table filtering
    
    'bridge/picnet_table_filter'

], function(search_suggest) {

    $(document).ready(function() {
        $('table#species').tableFilter();
    });

});
