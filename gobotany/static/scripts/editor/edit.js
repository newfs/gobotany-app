/* Routines to support editor pages. */

define([
    'bridge/jquery',
    'bridge/underscore',
    'editor/floatingtableheader'
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

        /* To display the /edit/cv/remaining-non-monocots/habitat/ page
           efficiently, we need to be very fast; this simple string
           concatenation seems to do quite well.  Note especially how we
           turn the vector ones and zeroes into lightweight check boxes
           in a single post-processing step! */

        var prefix = '<div><i>';
        var checked = '<b class="x">×</b>';
        var unchecked = '<b>×</b>';
        var marks = Array(character_values.length + 1).join('<b>×</b>');
        var suffix = '</i>' + marks + '</div>';

        var snippets = [];
        var names = _.keys(taxon_value_vectors);
        names.sort();
        _.each(names, function(scientific_name) {
            snippets.push('<div><i>');
            snippets.push(scientific_name);
            snippets.push('</i>');
            snippets.push(taxon_value_vectors[scientific_name]);
            snippets.push('</div>');
        });

        $('.pile-character-grid').html(
            snippets.join('')
                .replace(/0/g, unchecked)
                .replace(/1/g, checked)
        );
    };

    return exports;
});
