/* Routines to support editor pages. */

define([
    'bridge/jquery',
    'bridge/underscore'
], function(
    $, _
) {
    var exports = {};

    exports.setup_pile_character_page = function() {
        $(document).ready(function() {
            format_pile_character_page();
        });
    };

    var format_pile_character_page = function() {
        $('.pile-character-grid .value').each(function() {
            var $div = $('div', this);
            var h = $div.height();
            var w = $div.width();
            $(this).height(w);
            $div.width(h);
        });
    };

    return exports;
});
