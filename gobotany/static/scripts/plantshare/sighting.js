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

            var loc = first_result.geometry.location; // a Google Maps LatLng
            var latitude = loc.lat();
            var longitude = loc.lng();
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
        marker_map.use_marker_clusterer = false;
        marker_map.setup();
        
        // Add the primary marker for the sighting.
        var title = marker_map.center_title;
        var info_window_html = marker_map.center_title;
        marker_map.add_marker(marker_map.latitude, marker_map.longitude,
            title, info_window_html);

        // Add any secondary markers for place names mentioned in the
        // location notes.
        google_maps.event.addListener(marker_map.map, 'bounds_changed',
                                      function () {
            // Only run this function once, when the map initally loads.
            if (map_loaded == false) {
                map_loaded = true;

                var location_notes = $('#location-notes').text();
                var place_parser = new PlaceParser();
                var possible_places = place_parser.parse(location_notes);
                var MAX_PLACES_TO_GEOCODE = 3;
                var geocoder = new Geocoder();
                var bounds = marker_map.get_bounds();
                var places = possible_places.slice(0, MAX_PLACES_TO_GEOCODE);
                for (var i = 0; i < places.length; i++) {
                    var place = places[i];
                    if (place !== '') {
                        geocoder.geocode(places[i], mark_location, bounds);
                    }
                }
            }
        });

    });
});
