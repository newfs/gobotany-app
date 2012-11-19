define([
    'bridge/jquery',
    'mapping/google_maps',
    'mapping/sightings_map'
], function ($, google_maps, SightingsMap) {

    var MapsTest = function () {   // Constructor

        // Set up maps when the page has loaded.
        $(document).ready(function () {

            $('div.map[data-type="sightings"]').each(function () {
                var sightings_map = new SightingsMap(this);
                sightings_map.setup();
                sightings_map.mark_center();
            });

            // Set up basic sightings map centered on New England.
            var new_england_map_div = $('#new-england-map');
            var new_england_sightings_map =
                new SightingsMap(new_england_map_div);
            new_england_sightings_map.setup();
            new_england_sightings_map.mark_center();

            // Set up map for mini Sightings Locator.
            var mini_sightings_map_div = $('#mini-sightings-map');
            var mini_sightings_map = new SightingsMap(mini_sightings_map_div);
            mini_sightings_map.setup();
            mini_sightings_map.show_plant('Acer saccharum');

            // Set up map for Sightings Locator.
            var sightings_map_div = $('#sightings-map');
            var sightings_map = new SightingsMap(sightings_map_div);
            sightings_map.setup();
            sightings_map.show_plant('Nymphaea odorata');
        });
    };
        
    // Functions to test and repair a bug with an overlay mask.

    MapsTest.prototype.expose = function () {
        $(this).expose();
    };

    MapsTest.prototype.show_overlay = function () {
        $('#overlay-test').overlay({
            mask: {
                color: '#ccc',
                loadSpeed: 500,
                opacity: 0.5,
                top: 0
            },
            closeOnClick: true,
            load: true
        }).click(function (event) {
            $('#overlay-test').data('overlay').close();
        });
        $('#exposeMask').css('position', 'fixed');
    };

    // Return the constructor function.
    return MapsTest;
});

