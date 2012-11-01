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
        this.info_window = null;
    };

    SightingsMap.prototype.setup = function () {
        var lat_long = new google.maps.LatLng(this.latitude, this.longitude);
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

    SightingsMap.prototype.add_marker = function (latitude, longitude,
                                                  title, created, photos) {
        var lat_long = new google_maps.LatLng(latitude, longitude);
        var marker = new google.maps.Marker({
            position: lat_long,
            map: this.map,
            title: title
        });
        var html = '<div class="info-window"><p>' + title;
        if (created !== undefined) {
            html += ' (' + created + ')';
        }
        html += '</p>';
        if (photos !== undefined) {
            var photo_url = photos[0];
            html += ' <img src="' + photo_url + '">';
        }
        html += '</div>';
        var info_window = this.info_window;
        google_maps.event.addListener(marker, 'click', function () {
            info_window.setContent(html);
            info_window.open(this.map, marker);
        });
    };

    SightingsMap.prototype.mark_center = function () {
        this.add_marker(this.latitude, this.longitude, this.center_title);
    };

    SightingsMap.prototype.show_plant = function (plant_name) {
        // Get sightings data from the server and show them on the map.
        $.ajax({
            url: '/ps/api/sightings/?plant=' + plant_name,   // TODO: URL base
            context: this
        }).done(function (json) {
            for (var i = 0; i <= json.sightings.length; i++) {
                var sighting = json.sightings[i];
                var location = sighting.location;
                if (location === undefined) {
                    location = sighting.latitude + ', ' + sighting.longitude;
                }
                this.add_marker(sighting.latitude, sighting.longitude,
                                location, sighting.created, sighting.photos);
            }
        });
    };

    // Return the constructor function.
    return SightingsMap;
});
