define([
    'bridge/jquery',
    'plantshare/sightings_locator_part'
], function ($, SightingsLocatorPart) {

    /*
    $(document).ready(function () {
        var FIND_FORM_SELECTOR = '#find-people-form';
        $(FIND_FORM_SELECTOR + ' input[type=button]').click(function () {
            $(FIND_FORM_SELECTOR).submit();
        });

    });*/

    $(window).load(function () {   // maps must be created at onload

        var sightings_locator_part =
            new SightingsLocatorPart('#sightings-locator');
        sightings_locator_part.setup();
    });
});
