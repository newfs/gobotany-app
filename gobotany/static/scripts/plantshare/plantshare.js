define([
    'bridge/jquery',
    'plantshare/sightings_locator_part',
    'plantshare/ask_the_botanist'
], function ($, SightingsLocatorPart, x1) {

    $(window).load(function () {   // maps must be created at onload

        var sightings_locator_part =
            new SightingsLocatorPart('#sightings-locator');
        sightings_locator_part.setup();
    });
});
