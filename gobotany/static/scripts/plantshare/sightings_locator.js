// Sightings Locator page: initialization
define([
    'bridge/jquery',
    'plantshare/sightings_locator_part'
], function ($, SightingsLocatorPart) {

    $(window).load(function () {   // maps must be created at onload

        var sightings_locator_part =
            new SightingsLocatorPart('#sightings-locator');
        sightings_locator_part.setup();
    });
});
