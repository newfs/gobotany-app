/* Sightings Locator component part with an input box and map.
 *
 * Note:
 * The map requires that this be set up at onload, not at jQuery ready. */
define([
    'bridge/jquery',
    'bridge/jquery.cookie',
    'plantshare/sightings_map'
], function ($, x1, SightingsMap) {

    function SightingsLocatorPart(locator_element_css) {
        // Constructor
        
        this.$locator_element = $(locator_element_css);
        this.$plant_name_field = this.$locator_element.find(
            'input[type="text"]').first();
        this.current_plant_name = '';
        var plant_name = $.cookie('last_locator_name');
        if (plant_name !== undefined && plant_name.length > 0) {
            this.current_plant_name = plant_name;
            this.$plant_name_field.val(this.current_plant_name);
        }
    };

    SightingsLocatorPart.prototype.show_plant = function (plant_name,
                                                          sightings_map) {
        this.current_plant_name = plant_name;
        $.cookie('last_locator_name', this.current_plant_name,
            {path: '/'});
        sightings_map.show_plant(this.current_plant_name);
    };

    SightingsLocatorPart.prototype.setup = function () {
        // Set up the map and form.
        
        var map_div = this.$locator_element.find('.map').first();

        // Restore the last map location the user used, if any.
        var CENTER_COOKIE_NAME = 'last_locator_center';
        var sightings_map = new SightingsMap(map_div, CENTER_COOKIE_NAME);
        sightings_map.setup();

        // Restore the last plant searched in the Sightings Locator, if any.
        this.show_plant(this.current_plant_name, sightings_map);

        this.$locator_element.submit($.proxy(
            function (e) {
                e.preventDefault();  // prevent form submit because using AJAX

                var plant_name = this.$plant_name_field.val();
                if (plant_name !== this.current_plant_name) {
                    this.show_plant(plant_name, sightings_map);
                }
            }, this)
        );
    };

    // Return the constructor function.
    return SightingsLocatorPart;
});
