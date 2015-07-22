define([
    'bridge/jquery',
    'lib/picnet.table.filter.min',
    'util/shadowbox_init'
], function ($, table_filter, Shadowbox) {
    $(document).ready(function () {
        // Set up table filtering.
        var options = {
            enableCookies: true,
            filterDelay: 400,
            filteredRows: function () {
                // Update the message indicating how many sightings are shown.
                var ROWS_SELECTOR = '.list tbody tr';
                var num_rows = $(ROWS_SELECTOR).length;
                var num_hidden_rows = $(
                    ROWS_SELECTOR + '[style="display: none;"]').length;
                var num_showing = num_rows - num_hidden_rows;
                var message = '.';
                if (num_showing < num_rows) {
                    message = ', filtered to ' + num_showing + '.';
                }
                $('.showing').html(message);
            }
        };
        $('.content table').tableFilter(options);
    });
});
