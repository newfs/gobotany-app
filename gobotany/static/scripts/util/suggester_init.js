/* Activate any input boxes on the page that are to offer suggestions. */

define([
    'bridge/jquery',
    'util/suggester'
], function ($, Suggester) {

    $(document).ready(function () {
        $('input.suggest').each(function () {
            var suggester = new Suggester(this);
            suggester.setup();
        });
    });
});
