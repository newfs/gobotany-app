define([
    'bridge/jquery',
    'mapping/google_maps',
    'mapping/sightings_map'
], function ($, google_maps, SightingsMap) {

    function SightingsLocator(locator_element_css) {
        // Constructor
        
        this.$locator_element = $(locator_element_css);
        this.current_plant_name = '';
    };

    SightingsLocator.prototype.setup = function () {
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
                    console.log('about to fetch sightings for',
                        this.current_plant_name);
                    sightings_map.show_plant(this.current_plant_name);
                }

            }, this)
        );
    };

    // Return the constructor function.
    return SightingsLocator;
});
