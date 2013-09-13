/* Map for plant sightings in PlantShare.
 *
 * Note:
 * The map requires that this be set up at onload, not at jQuery ready. */

define([
    'bridge/jquery',
    'mapping/marker_map'
], function ($, MarkerMap) {

    // Constructor
    function SightingsMap(map_div, cookie_names) {
        // Call the super-constructor.
        MarkerMap.apply(this, arguments);

        this.cookie_names = cookie_names;
        this.MAX_INFO_DESC_LENGTH = 70;

        return this;
    };

    // Extend the base

    function subclass_of(base) {
        _subclass_of.prototype = base.prototype;
        return new _subclass_of();
    }
    function _subclass_of() {};

    SightingsMap.prototype = subclass_of(MarkerMap);

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
            html += ' <img src="' + photo_url + '">';
        }
        html += '<p>';
        if (sighting.description !== undefined &&
            sighting.description.length > 0) {
        
            var description = sighting.description.substr(0,
                this.MAX_INFO_DESC_LENGTH);
            if (sighting.description.length > this.MAX_INFO_DESC_LENGTH) {
                description += '... ';
            }
            html += description;
        }
        var more_link = '<a href="/plantshare/sightings/' + sighting.id +
            '/">more</a>'; 
        if (sighting.id !== undefined) {
            if (sighting.description.length > 0) {
                html += more_link;
                html += '</p>';
            }
            else {
                html += '<p>' + more_link + '</p>';
            }
        }
        html += '</div>';
        return html;
    };

    SightingsMap.prototype.show_sightings_count = function (sightings_count) {
        // On the mini map, the status message must be placed in view.
        $('#sightings-status').css('margin-left', 'auto');

        // Show the status message with sightings count.
        $('#sightings-status').show();
        $('#sightings-status').css('color', '#000');
        $('#sightings-status span').html(sightings_count);
    };

    SightingsMap.prototype.show_sightings = function (plant_name) {
        // Get sightings data from the server and show them on the map.
        var url = '/plantshare/api/sightings/'

        // If the plant_name is undefined or null, will leave off the
        // plant parameter and show recent sightings. If the plant name
        // is non-empty or empty, will include the plant parameter and
        // show sightings for that query.
        var show_plant = (plant_name !== undefined && plant_name !== null);
        if (show_plant) {
            url += '?plant=' + plant_name
        }
        $.ajax({
            url: url,
            context: this
        }).done(function (json) {
            this.clear_markers();
            var sightings_count = json.sightings.length;
            if (show_plant) {
                this.show_sightings_count(sightings_count);
            }
            var marker;
            for (var i = 0; i < sightings_count; i++) {
                var sighting = json.sightings[i];
                var name = sighting.identification;
                var title = this.get_sighting_title(name, sighting, false);
                var info_window_html = this.build_info_window_html(name,
                                                                   sighting);

                // Determine whether to show the info window for this
                // sighting: do so if it was stored as the last viewed.
                var show_info = false;
                var last_sighting_id = parseInt(
                    $.cookie(this.cookie_names['last_viewed']));
                if (last_sighting_id === sighting.id) {
                    show_info = true;
                }

                marker = this.add_marker(sighting.latitude,
                    sighting.longitude, title, info_window_html, sighting.id,
                    show_info);
            }
        });
    };

    SightingsMap.prototype.show_sighting = function (sighting_id,
            cookie_names) {
        // Show a single recent sighting on the map.
        var url = '/plantshare/api/sightings/?id=' + sighting_id;
        $.ajax({
            url: url,
            context: this
        }).done(function (json) {
            // Clear any markers, the plant name box, and the search
            // results status message.
            this.clear_markers();
            $('#plant-name').val('');
            var color = $('#sightings-status').css('background-color');
            $('#sightings-status').css('color', color);

            // Add a marker for the sighting and pan to show it.
            var marker;
            var sighting = json.sightings[0];
            var name = sighting.identification;
            var title = this.get_sighting_title(name, sighting, false);
            var info_window_html = this.build_info_window_html(name,
                                                               sighting);
            var show_info = true;
            marker = this.add_marker(sighting.latitude,
                sighting.longitude, title, info_window_html, sighting.id,
                show_info);
            this.pan_to(sighting.latitude, sighting.longitude);
        });
    };

    // Return the constructor function.
    return SightingsMap;
});

