/* Map for plant sightings in PlantShare.
 *
 * Note:
 * The map requires that this be set up at onload, not at jQuery ready. */

define([
    'bridge/jquery',
    'mapping/google_maps'
], function ($, google_maps) {

    // Constructor
    function SightingsMap(map_div) {
        this.MAX_INFO_DESC_LENGTH = 80;

        this.$map_div = $(map_div);
        this.map_id = this.$map_div.attr('id');
        this.latitude = this.$map_div.attr('data-latitude');
        this.longitude = this.$map_div.attr('data-longitude');
        this.center_title = this.$map_div.attr('data-center-title');
        this.map = null;
        this.info_window = null;
        this.markers = [];
    };

    SightingsMap.prototype.setup = function () {
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

    SightingsMap.prototype.get_sighting_title = function (plant_name,
                                                          sighting) {
        var location = sighting.location;
        if (location === undefined || location.length === 0) {
            location = sighting.latitude + ', ' + sighting.longitude;
        }
        return '<i>' + plant_name + '</i> at ' + location;
    };

    SightingsMap.prototype.build_info_window_html = function (plant_name,
                                                              sighting) {
        var title = this.get_sighting_title(plant_name, sighting);
        var html = '<div class="info-window"><h5>' + title + '</h5>';
        if (sighting.user !== undefined) {
            html += '<p>by ' + sighting.user;
            if (sighting.created !== undefined) {
                html += ' on ' + sighting.created;
            }
            html += '</p>';
        }
        if (sighting.photos !== undefined && sighting.photos.length > 0) {
            var photo_url = sighting.photos[0];
            console.log('photo_url:', photo_url);
            html += ' <img src="' + photo_url + '">';
        }
        html += '<p>';
        if (sighting.description !== undefined &&
            sighting.description.length > 0) {
        
            var description = sighting.description.substr(0,
                this.MAX_INFO_DESC_LENGTH);
            if (sighting.description.length > this.MAX_INFO_DESC_LENGTH) {
                description += '...';
            }
            html += description;
        }
        html += '</p>';
        if (sighting.id !== undefined) {
            html += '<p><a href="/ps/sightings/' + sighting.id +
                    '/">more</a></p>';
        }
        html += '</div>';
        return html;
    };

    SightingsMap.prototype.clear_markers = function () {
        // Clear the stored array of markers to clear them from the map.
        if (this.markers) {
            for (i in this.markers) {
                this.markers[i].setMap(null);
            }
        }
    };

    SightingsMap.prototype.add_marker = function (latitude, longitude, title,
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

    SightingsMap.prototype.mark_center = function () {
        this.add_marker(this.latitude, this.longitude, this.center_title);
    };

    SightingsMap.prototype.show_plant = function (plant_name) {
        // Get sightings data from the server and show them on the map.
        $.ajax({
            url: '/ps/api/sightings/?plant=' + plant_name,   // TODO: URL base
            context: this
        }).done(function (json) {
            this.clear_markers();
            for (var i = 0; i < json.sightings.length; i++) {
                var sighting = json.sightings[i];
                var title = this.get_sighting_title(plant_name, sighting);
                var info_window_html = this.build_info_window_html(plant_name,
                                                                   sighting);
                this.add_marker(sighting.latitude, sighting.longitude,
                                title, info_window_html);
            }
        });
    };

    // Return the constructor function.
    return SightingsMap;
});
