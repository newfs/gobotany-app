/* Sightings Locator component part with an input box and map.
 *
 * Note:
 * The map requires that this be set up at onload, not at jQuery ready. */
define([
    'bridge/jquery',
    'mapping/sightings_map'
], function ($, SightingsMap) {

    function SightingsLocatorPart(locator_element_css) {
        // Constructor
        
        this.$locator_element = $(locator_element_css);
        this.current_plant_name = '';
    };

    SightingsLocatorPart.prototype.setup = function () {
        // Set up the map and form.
        
        var map_div = this.$locator_element.find('.map').eq(0);
        var sightings_map = new SightingsMap(map_div);
        sightings_map.setup();

        this.$locator_element.submit($.proxy(
            function (e) {
                e.preventDefault();  // prevent form submit because using AJAX

                var plant_name = this.$locator_element.find(
                    'input[type="text"]').eq(0).val();

                if (plant_name !== this.current_plant_name) {
                    this.current_plant_name = plant_name;
                    sightings_map.show_plant(this.current_plant_name);
                }

            }, this)
        );
    };

    // Return the constructor function.
    return SightingsLocatorPart;
});
