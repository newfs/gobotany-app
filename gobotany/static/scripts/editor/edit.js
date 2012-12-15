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
        var snippets = [];
        var names = _.keys(taxon_value_vectors);
        names.sort();

        _.each(names, function(scientific_name) {
            snippets.push('<div><i>');
            snippets.push(scientific_name);
            snippets.push('</i><span>expand ▶</span>');
            snippets.push(taxon_value_vectors[scientific_name]);
            snippets.push('</div>');
        });

        $grid.html(
            snippets.join('')
                .replace(/0/g, '<b>×</b>')
                .replace(/1/g, '<b class="x">×</b>')
        );

        $(document).on('click', '.pile-character-grid b', function() {
            $(this).toggleClass('x');
        });

        /* Split bigrow when there are many character values. */

        var $headers = $('.pile-character-bigrow div');

        if ($headers.length > 15) {
            var half = $headers.length / 2;
            var halfint = Math.ceil(half);
            var $a = $headers.eq(0);
            var $b = $headers.eq(halfint);
            var offset = $a.position().top - $b.position().top;
            if (half == halfint) {
                $b.css('margin-top', offset);
            } else {
                $b.css('margin-top', offset - offset / halfint);
            }
        }

        /* Expand the row that is currently hovered. */

        var $bigrow = $('.pile-character-bigrow').remove();
        var replaced_div = null;

        $(document).on('mouseenter', '.pile-character-grid > div', function() {
            return;
            var $div = $(this);
            if ($div.hasClass('column'))
                return;
            if ($div.hasClass('pile-character-bigrow'))
                return;
            if (replaced_div !== null)
                $bigrow.replaceWith(replaced_div);
            replaced_div = this;
            $div.replaceWith($bigrow);

            var scientific_name = $div.find('i').text();
            $bigrow.find('i').text(scientific_name);
        });

        /* Simulate a mouseover highlight on the current column. */

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

        /* Keep the grid header always in view. */

    };

    return exports;
});
