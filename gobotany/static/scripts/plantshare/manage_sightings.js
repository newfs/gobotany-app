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
                var num_rows = $('.list tbody tr').length;
                var num_hidden_rows = $(
                    '.list tbody tr[style="display: none;"]').length;
                var num_showing = num_rows - num_hidden_rows;
                var message = 'are all';
                if (num_showing < num_rows) {
                    var verb = (num_showing > 1) ? 'are': 'is';
                    message = verb + ' ' + num_showing + ' of the';
                }
                $('.showing').html(message);
            }
        };
        $('.content table').tableFilter(options);
    });
});
