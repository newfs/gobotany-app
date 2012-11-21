define([
    'bridge/jquery',
    'mapping/google_maps',
    'mapping/sightings_map'
], function ($, google_maps, SightingsMap) {

    $(document).ready(function () {

        // Set up the map and form for the full size Sightings Locator.

        var sightings_map_div = $('#sightings-locator #sightings-map');
        var sightings_map = new SightingsMap(sightings_map_div);
        sightings_map.setup();

        $('form#sightings-locator').submit(function (e) {
            e.preventDefault();   // prevent form submit

            console.log('TODO: call the server for sightings data');
            sightings_map.show_plant('Acer saccharum');
        });

    });
});
