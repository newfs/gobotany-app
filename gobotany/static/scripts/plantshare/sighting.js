define([
    'bridge/jquery',
    'mapping/geocoder',
    'mapping/google_maps',
    'mapping/marker_map',
    'mapping/place_parser'
], function ($, Geocoder, google_maps, MarkerMap, PlaceParser) {

    var marker_map;
    var map_loaded = false;

    function mark_location(results, status) {
        if (results[0]) {
            var first_result = results[0];

            var latitude = first_result.geometry.location.jb;
            var longitude = first_result.geometry.location.kb;
            var title = first_result.formatted_address;

            // If this location differs from the sighting location,
            // add a marker for it.
            if (parseFloat(latitude) !== parseFloat(marker_map.latitude) &&
                parseFloat(longitude) !== parseFloat(marker_map.longitude)) {
                marker_map.add_landmark_marker(latitude, longitude, title);
            }
        }
    }

    $(window).load(function () {
        // The maps and geocoder must be created at page "onload."

        var map_div = $('.map').first();
        var cookie_names = {};
        marker_map = new MarkerMap(map_div, cookie_names);
        marker_map.setup();
        marker_map.mark_center();

        google_maps.event.addListener(marker_map.map, 'bounds_changed',
                                      function () {
            // Only run this function once, when the map initally loads.
            if (map_loaded == false) {
                map_loaded = true;

                // If location notes were provided, try parsing them for
                // possible place names for which a map marker in a secondary
                // color can be set.
                var location_notes = $('#location-notes').text();

                var place_parser = new PlaceParser();
                var possible_places = place_parser.parse(location_notes);

                var MAX_PLACES_TO_GEOCODE = 3;
                var geocoder = new Geocoder();
                var bounds = marker_map.get_bounds();
                var places = possible_places.slice(0, MAX_PLACES_TO_GEOCODE);
                for (var i = 0; i < places.length; i++) {
                    geocoder.geocode(places[i], mark_location, bounds);
                }
            }
        });

    });
});
