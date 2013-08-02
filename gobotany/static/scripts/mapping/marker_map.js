/* Base for a map that can display markers.
 *
 * Note:
 * The map requires that this be set up at onload, not at jQuery ready.
 *
 * To use this base, you may wish to inherit from it and write code that
 * can add your markers and marker popups if desired. */

define([
    'bridge/jquery',
    'bridge/jquery.cookie',
    'mapping/google_maps'
], function ($, x1, google_maps) {

    // Constructor
    function MarkerMap(map_div, cookie_names) {
        var DEFAULT_ZOOM_LEVEL = 6;

        // Set limits for latitude and longitude roughly corresponding to
        // North America. Upon restoring the map location, if the
        // location is found to be out of these limits, the default
        // center location will be used instead.
        var MIN_LATITUDE = 24;
        var MAX_LATITUDE = 60;
        var MIN_LONGITUDE = -128;
        var MAX_LONGITUDE = -53;

        this.$map_div = $(map_div);
        this.map_id = this.$map_div.attr('id');

        this.latitude = this.$map_div.attr('data-latitude');
        this.longitude = this.$map_div.attr('data-longitude');
        // If the last location center was saved in a cookie, restore it.
        this.center_cookie_name = cookie_names['center'];
        var center_lat_long = $.cookie(this.center_cookie_name);
        if (center_lat_long !== undefined && center_lat_long !== null) {
            center_lat_long = center_lat_long.replace(/\(|\)/g, '');
            var parts = center_lat_long.split(',');
            var latitude = parts[0].trim();
            var longitude = parts[1].trim();
            if (latitude === undefined || isNaN(latitude) || 
                longitude === undefined || isNaN(longitude) ||
                latitude < MIN_LATITUDE || latitude > MAX_LATITUDE ||
                longitude < MIN_LONGITUDE || longitude > MAX_LONGITUDE) {
                // If a location part is invalid, clear it.
                console.error('Invalid location part. Clearing cookie');
                $.cookie(this.center_cookie_name, null, {path: '/'});
            }
            else {
                var lat_long = new google_maps.LatLng(latitude, longitude);
                this.latitude = lat_long.lat();
                this.longitude = lat_long.lng();
            }
        }

        this.zoom = DEFAULT_ZOOM_LEVEL;

        // If the page has a zoom level specified, start with it.
        var zoom = this.$map_div.attr('data-zoom');
        if (zoom) {
            this.zoom = parseInt(zoom);
        }

        // If the last zoom level was saved in a cookie, restore it.
        this.zoom_cookie_name = cookie_names['zoom'];
        zoom = $.cookie(this.zoom_cookie_name);
        if (zoom !== undefined && zoom !== null) {
            if (isNaN(zoom)) {
                // If a zoom level is invalid, clear it.
                console.error('Invalid zoom level. Clearing cookie');
                $.cookie(this.zoom_cookie_name, null, {path: '/'});
            }
            else {
                this.zoom = parseInt(zoom);
            }
        }

        this.last_viewed_cookie_name = cookie_names['last_viewed'];
        this.center_title = this.$map_div.attr('data-center-title');
        this.map = null;
        this.info_window = null;    // InfoWindow: marker pop-up
        this.markers = [];
    };

    MarkerMap.prototype.setup = function () {
        var lat_long = new google_maps.LatLng(this.latitude, this.longitude);
        var map_options = {
            center: lat_long,
            zoom: this.zoom,
            mapTypeId: google_maps.MapTypeId.ROADMAP,
            mapTypeControl: true,
            mapTypeControlOptions: {
                style: google_maps.MapTypeControlStyle.DROPDOWN_MENU
            }
        };
        this.map = new google_maps.Map(this.$map_div.get(0), map_options);

        // When the user moves the map around, store the location center.
        var center_cookie_name = this.center_cookie_name;
        google_maps.event.addListener(
            this.map, 'center_changed', function () {
                var center = this.center.toString();
                $.cookie(center_cookie_name, center, {path: '/'});
        });
        // When the user changes the zoom level, store it.
        var zoom_cookie_name = this.zoom_cookie_name;
        google_maps.event.addListener(
            this.map, 'zoom_changed', function () {
                $.cookie(zoom_cookie_name, this.zoom, {path: '/'});
        });      

        var info_window_options = {
            maxWidth: 300
        };
        this.info_window = new google_maps.InfoWindow(info_window_options);

        // When the user clicks anywhere outside an open info window,
        // close the window.
        var info_window = this.info_window;
        google_maps.event.addListener(this.map, 'click', function () {
            info_window.close();
        });
    };

    MarkerMap.prototype.clear_markers = function () {
        // Clear the stored array of markers to clear them from the map.
        if (this.markers) {
            for (i in this.markers) {
                this.markers[i].setMap(null);
            }
        }
    };

    MarkerMap.prototype.save_last_viewed = function (last_viewed_id,
                                                     cookie_name) {
        if (last_viewed_id !== undefined && last_viewed_id !== null) {
            // Set a cookie for the last viewed item, for restoring later.
            $.cookie(cookie_name, last_viewed_id, {path: '/'});
        }
    };

    MarkerMap.prototype.get_bounds = function () {
        var bounds = this.map.getBounds();
        return bounds;
    };

    MarkerMap.prototype.add_landmark_marker = function (latitude, longitude,
                                                        title) {
        // Create a marker in a secondary color to mark a landmark.
        var BASE = '//';   // base for protocol-relative URL
        var pin_image = new google_maps.MarkerImage(BASE +
            location.host + "/static/images/icons/marker-pin-gray.png",
            new google.maps.Size(20, 34),
            new google.maps.Point(0, 0),
            new google.maps.Point(10, 34)
        );
        var pin_shadow = new google_maps.MarkerImage(BASE +
            location.host + "/static/images/icons/marker-pin-shadow.png",
            new google.maps.Size(40, 37),
            new google.maps.Point(0, 0),
            new google.maps.Point(12, 35)
        );
        var marker = new google_maps.Marker({
            position: new google_maps.LatLng(latitude, longitude), 
            map: this.map,
            icon: pin_image,
            shadow: pin_shadow,
            title: title
        });

        // Show title in an information popup upon clicking the marker.
        var info_window = this.info_window;
        google_maps.event.addListener(marker, 'click', function () {
            info_window.setContent(title);
            info_window.open(this.map, marker);
        });

        this.markers.push(marker);
    };

    MarkerMap.prototype.add_marker = function (latitude, longitude, title,
                                               info_window_html, sighting_id,
                                               show_info) {
        // Create a marker and add it to the array of markers that must
        // be kept in order to be able to clear all markers.
        var lat_long = new google_maps.LatLng(latitude, longitude);
        var marker = new google_maps.Marker({
            position: lat_long,
            map: this.map,
            title: title
        });
        this.markers.push(marker);

        // Allow for showing an information popup upon clicking a marker.
        var info_window = this.info_window;
        var save_last_viewed = this.save_last_viewed;
        var cookie_name = this.last_viewed_cookie_name;
        google_maps.event.addListener(marker, 'click', function () {
            info_window.setContent(info_window_html);
            info_window.open(this.map, marker);
            save_last_viewed(sighting_id, cookie_name);
        });

        if (show_info === true) {
            // Show the info window upon adding this marker.
            info_window.setContent(info_window_html);
            info_window.open(this.map, marker);
            save_last_viewed(sighting_id, cookie_name);
        }
    };

    MarkerMap.prototype.mark_center = function () {
        this.add_marker(this.latitude, this.longitude, this.center_title);
    };

    // Return the constructor function.
    return MarkerMap;
});
