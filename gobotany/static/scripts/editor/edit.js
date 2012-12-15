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

        var $grid = $('.pile-character-grid');

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

        $grid.html(
            snippets.join('')
                .replace(/0/g, unchecked)
                .replace(/1/g, checked)
        );

        $(document).on('click', '.pile-character-grid b', function() {
            $(this).toggleClass('x');
        });

        /* Split a heading that has too many character values. */

        var $headers = $('.pile-character-header div');

        if ($headers.length > 15) {
            var half = $headers.length / 2;
            var halfint = Math.floor(half);
            var $a = $headers.eq(0);
            var $b = $headers.eq(halfint);
            var offset = $a.position().top - $b.position().top;
            if (half == halfint) {
                $b.css('margin-top', offset);
            } else {
                $a.css('margin-top', - offset / halfint);
                $b.css('margin-top', offset + offset / halfint);
            }
        }

        /* Highlight */

        var $column = $('<div>', {'class': 'column'}).appendTo($grid);

        $(document).on('mouseover', '.pile-character-grid b', function() {
            $column.css({
                top: 0,
                bottom: 0,
                left: $(this).position().left,
                right: $(this).parent().width() - $(this).position().left -
                    $(this).outerWidth()
                });
        });
    };

    return exports;
});
