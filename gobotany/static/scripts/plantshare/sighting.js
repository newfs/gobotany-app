define([
    'bridge/jquery',
    'mapping/marker_map',
    'mapping/geocoder',
    'mapping/google_maps'
], function ($, MarkerMap, Geocoder, google_maps) {

    var marker_map;
    var map_loaded = false;

    function mark_location(results, status) {
        if (results[0]) {
            var first_result = results[0];

            var latitude = first_result.geometry.location.jb;
            var longitude = first_result.geometry.location.kb;
            var title = first_result.formatted_address;

            marker_map.add_landmark_marker(latitude, longitude, title);
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

                // If location notes were provided, try parsing them for a
                // possible location name for which a map marker in a
                // secondary color can be set.
                var location_notes = $('#location-notes').text();

                var EXCLUDE_WORDS = ['about', 'above', 'around', 'below',
                    'just', 'near', 'next', 'not', 'past', 'under'];
                var possible_location = '';
                var parts = location_notes.split(' ');
                for (var i = 0; i < parts.length; i++) {
                    var part = parts[i];
                    var first_char = part.slice(0, 1);
                    // Only consider uppercase words for a possible location.
                    if (first_char === first_char.toUpperCase()) {
                        // Include the word if not in the "exclude" list.
                        if ($.inArray(part.toLowerCase(),
                                      EXCLUDE_WORDS) === -1) {
                            possible_location += ' ' + part;
                        }
                    }
                }

                if (possible_location) {
                    var geocoder = new Geocoder();
                    var bounds = marker_map.get_bounds();
                    geocoder.geocode(possible_location, mark_location,
                        bounds);
                }
            }
        });

    });
});
