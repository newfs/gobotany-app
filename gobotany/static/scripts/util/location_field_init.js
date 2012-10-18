/* Activate any input boxes on the page that are to update a location map. */

define([
    'bridge/jquery',
    'util/location_field'
], function ($, LocationField) {

    $(document).ready(function () {
        $('input.location').each(function () {
            var location_field = new LocationField(this);
            location_field.setup();
        });
    });
});
