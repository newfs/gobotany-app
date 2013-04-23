define([
    'bridge/jquery',
    'lib/picnet.table.filter.min',
    'util/shadowbox_init'
], function ($, table_filter, Shadowbox) {
    $(document).ready(function () {
        // Set up table filtering.
        var options = {
            enableCookies: true,
            filterDelay: 400
        };
        $('.content table').tableFilter(options);
    });
});
