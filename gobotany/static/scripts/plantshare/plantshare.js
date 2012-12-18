define([
    'bridge/jquery',
    'plantshare/sightings_locator'
], function ($, SightingsLocator) {

    $(window).load(function () {   // maps must be created at onload

        var sightings_locator = new SightingsLocator('#sightings-locator');
        sightings_locator.setup();
    });
});
