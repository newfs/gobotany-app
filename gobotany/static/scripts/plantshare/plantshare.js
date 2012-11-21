define([
    'bridge/jquery',
    'mapping/google_maps',
    'mapping/sightings_map'
], function ($, google_maps, SightingsMap) {

    $(document).ready(function () {

        // Set up the map and form for the mini Sightings Locator.

        var mini_sightings_map_div = $('#sightings-locator.mini .map');
        var mini_sightings_map = new SightingsMap(mini_sightings_map_div);
        mini_sightings_map.setup();

        $('#sightings-locator.mini form').submit(function (e) {
            e.preventDefault();   // prevent form submit

            console.log('TODO: call the server for sightings data');
            mini_sightings_map.show_plant('Acer saccharum');
        });

    });
});
