define([
    'lib/picnet.table.filter.min'
], function () {
    $(document).ready(function () {
        var options = {
            enableCookies: true,
            filterDelay: 400
        };
        $('.content table').tableFilter(options);
    });
});
