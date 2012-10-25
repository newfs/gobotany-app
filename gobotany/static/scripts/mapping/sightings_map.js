/* Map for plant sightings in PlantShare */

define([
    'bridge/jquery',
    'mapping/google_maps'
], function ($, google_maps) {

    // Constructor
    function SightingsMap(map_div) {
        this.$map_div = $(map_div);
        this.map_id = this.$map_div.attr('id');
        this.latitude = this.$map_div.attr('data-latitude');
        this.longitude = this.$map_div.attr('data-longitude');
        this.center_title = this.$map_div.attr('data-center-title');
        this.map = null;
    };

    SightingsMap.prototype.setup = function () {
        var lat_long = new google.maps.LatLng(this.latitude, this.longitude);
        var map_options = {
            center: lat_long,
            zoom: 6,
            mapTypeId: google_maps.MapTypeId.ROADMAP
        };
        this.map = new google_maps.Map(this.$map_div.get(0), map_options);
    };

    SightingsMap.prototype.add_marker = function (latitude, longitude,
                                                  title) {
        var lat_long = new google_maps.LatLng(latitude, longitude);
        var marker = new google.maps.Marker({
            position: lat_long,
            map: this.map,
            title: title
        });
    };

    SightingsMap.prototype.mark_center = function () {
        this.add_marker(this.latitude, this.longitude, this.center_title);
    };

    // Return the constructor function.
    return SightingsMap;
});
