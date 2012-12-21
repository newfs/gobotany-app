/* Base for a map that can display markers.
 *
 * Note:
 * The map requires that this be set up at onload, not at jQuery ready.
 *
 * To use this base, you may wish to inherit from it and write code that
 * can add your markers and marker popups if desired. */

define([
    'bridge/jquery',
    'mapping/google_maps'
], function ($, google_maps) {

    // Constructor
    function MarkerMap(map_div) {
        this.$map_div = $(map_div);
        this.map_id = this.$map_div.attr('id');
        this.latitude = this.$map_div.attr('data-latitude');
        this.longitude = this.$map_div.attr('data-longitude');
        this.center_title = this.$map_div.attr('data-center-title');
        this.map = null;
        this.info_window = null;    // InfoWindow: marker pop-up
        this.markers = [];
    };

    MarkerMap.prototype.setup = function () {
        var lat_long = new google_maps.LatLng(this.latitude, this.longitude);
        var map_options = {
            center: lat_long,
            zoom: 6,
            mapTypeId: google_maps.MapTypeId.ROADMAP
        };
        this.map = new google_maps.Map(this.$map_div.get(0), map_options);
        var info_window_options = {
            maxWidth: 300
        };
        this.info_window = new google_maps.InfoWindow(info_window_options);
    };

    MarkerMap.prototype.clear_markers = function () {
        // Clear the stored array of markers to clear them from the map.
        if (this.markers) {
            for (i in this.markers) {
                this.markers[i].setMap(null);
            }
        }
    };

    MarkerMap.prototype.add_marker = function (latitude, longitude, title,
                                               info_window_html) {
        // Create a marker and add it to the array of markers that must
        // be kept in order to be able to clear all markers.
        var lat_long = new google_maps.LatLng(latitude, longitude);
        var marker = new google_maps.Marker({
            animation: google_maps.Animation.DROP,
            position: lat_long,
            map: this.map,
            title: title
        });
        this.markers.push(marker);

        // Allow for showing an information popup upon clicking a marker.
        var info_window = this.info_window;
        google_maps.event.addListener(marker, 'click', function () {
            info_window.setContent(info_window_html);
            info_window.open(this.map, marker);
        });
    };

    MarkerMap.prototype.mark_center = function () {
        this.add_marker(this.latitude, this.longitude, this.center_title);
    };

    // Return the constructor function.
    return MarkerMap;
});
