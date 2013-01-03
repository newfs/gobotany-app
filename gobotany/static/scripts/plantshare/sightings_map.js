/* Map for plant sightings in PlantShare.
 *
 * Note:
 * The map requires that this be set up at onload, not at jQuery ready. */

define([
    'bridge/jquery',
    'mapping/marker_map'
], function ($, MarkerMap) {

    // Constructor
    function SightingsMap(map_div) {
        MarkerMap.call(this, map_div);   // Call super-constructor

        this.MAX_INFO_DESC_LENGTH = 80;

        return this;
    };

    // Extend the base
    SightingsMap.prototype = new MarkerMap;
    SightingsMap.prototype.constructor = SightingsMap;

    // Define methods
    
    SightingsMap.prototype.get_sighting_title = function (plant_name,
                                                          sighting,
                                                          italicize_name) {
        var location = sighting.location;
        if (location === undefined || location.length === 0) {
            location = sighting.latitude + ', ' + sighting.longitude;
        }
        if (italicize_name === true) {
            plant_name = '<i>' + plant_name + '</i>';
        }
        return plant_name + ' at ' +
            location.charAt(0).toUpperCase() + location.substring(1);
    };

    SightingsMap.prototype.build_info_window_html = function (plant_name,
                                                              sighting) {
        var title = this.get_sighting_title(plant_name, sighting, true);
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

    SightingsMap.prototype.show_sightings_count = function (sightings_count) {
        $('#sightings-status').css('margin-left', 'auto'); // for the mini map

        $('#sightings-status').show();
        $('#sightings-status span').html(sightings_count);
    };

    SightingsMap.prototype.show_plant = function (plant_name) {
        // Get sightings data from the server and show them on the map.
        $.ajax({
            url: '/ps/api/sightings/?plant=' + plant_name,   // TODO: URL base
            context: this
        }).done(function (json) {
            this.clear_markers();
            var sightings_count = json.sightings.length;
            this.show_sightings_count(sightings_count);
            for (var i = 0; i < sightings_count; i++) {
                var sighting = json.sightings[i];
                var title = this.get_sighting_title(plant_name, sighting,
                                                    false);
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

