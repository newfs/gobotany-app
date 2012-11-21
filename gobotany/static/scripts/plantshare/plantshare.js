define([
    'bridge/jquery',
    'plantshare/sightings_locator'
], function ($, SightingsLocator) {

    $(document).ready(function () {

        var sightings_locator = new SightingsLocator('#sightings-locator');
        sightings_locator.setup();
    });
});
