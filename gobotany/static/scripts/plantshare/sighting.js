define([
    'bridge/jquery',
    'mapping/marker_map'
], function ($, MarkerMap) {

    $(window).load(function () {   // maps must be created at onload

        var map_div = $('.map').first();
        var cookie_names = {};
        var marker_map = new MarkerMap(map_div, cookie_names);
        marker_map.setup();

        marker_map.mark_center();
    });
});
