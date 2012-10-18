/* Support updating a location map upon changing a location input field.
 *
 * The expected HTML id of the map is that of the input field with
 * "_map" appended to it.
 *
 * */

define([
    'bridge/jquery'
], function ($) {

    function LocationField(input_box) {
        // Constructor

        this.$input_box = $(input_box);
        this.$input_box_id = this.$input_box.attr('id');
        this.$location_map_id = this.$input_box_id + '_map';
        this.$location_map = $('#' + this.$location_map_id);
    };

    LocationField.prototype.setup = function () {
        // If there is a map for this location input field, update the map
        // when focus shifts away from the field.
        // (TODO: decide whether to also call this on some other events, such
        // as pressing Enter, automatically on change after a delay, etc.)
        if (this.$location_map !== undefined) {
            this.$input_box.blur($.proxy(this.update_map, this));
        }
    };

    LocationField.prototype.update_map = function () {
        // Update the map if necessary.
        var location_input_value = this.$input_box.val();
        if (location_input_value !== '') {

            var current_map_location =
                this.$location_map.attr('alt').slice(5);

            if (location_input_value !== current_map_location) {

                // Update map URL.
                var current_map_url = this.$location_map.attr('src');
                var new_map_url = current_map_url.replace(
                    current_map_location, location_input_value);
                this.$location_map.attr('src', new_map_url);

                // Update map image alt text.
                this.$location_map.attr('alt',
                                        'Map: ' + location_input_value);
            }
        }
    };

    // Return the constructor function.
    return LocationField;
});
