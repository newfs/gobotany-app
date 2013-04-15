define([
    'bridge/jquery',
    'lib/picnet.table.filter.min',
    'util/shadowbox_init'
], function ($, table_filter, Shadowbox) {
    $(document).ready(function () {
        // Set up Delete links.
        Shadowbox.setup('a.delete');

        // Set up table filtering.
        var options = {
            enableCookies: true,
            filterDelay: 400
        };
        $('.content table').tableFilter(options);
    });
});
