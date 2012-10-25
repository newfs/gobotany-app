define([
    'bridge/jquery',
    'util/google_maps'
], function ($, google_maps) {

    function make_map(latitude, longitude, id, marker_title) {
        var lat_long = new google.maps.LatLng(latitude, longitude);
        var map_options = {
            center: lat_long,
            zoom: 6,
            mapTypeId: google_maps.MapTypeId.ROADMAP
        };
        var map = new google_maps.Map($('#' + id).get(0), map_options);
        var marker = new google.maps.Marker({
            position: lat_long,
            map: map,
            title: marker_title
        });
    }

    $(document).ready(function () {
        var latitude = 44.53599,
            longitude = -70.56609,
            id = 'map-new-england',
            marker_title = 'Rumford, Maine';
        make_map(latitude, longitude, id, marker_title);
    });
});
