// Sightings Locator page: initialization
define([
    'bridge/jquery',
    'mapping/google_maps', // request maps module before creating map control
    'plantshare/sightings_locator_part',
    'util/activate_smooth_div_scroll'
], function ($, google_maps, SightingsLocatorPart, activate_scroll) {

    $(window).load(function () {   // maps must be created at onload

        var sightings_locator_part =
            new SightingsLocatorPart('#sightings-locator');
        sightings_locator_part.setup();
    });
});
