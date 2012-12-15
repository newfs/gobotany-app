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
            build_grid_from_json();
            install_hover_column();
            install_value_tip();
            install_click_handlers();
            install_expand_button();
            split_huge_bigrow();
        });
    };

    var build_grid_from_json = function() {

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
            var ones_and_zeroes = taxon_value_vectors[scientific_name];
            snippets.push('<div><i>');
            snippets.push(scientific_name);
            snippets.push('</i>');
            snippets.push(ones_and_zeroes);
            snippets.push('</div>');
        });

        $grid.html(
            snippets.join('')
                .replace(/0/g, '<b>×</b>')
                .replace(/1/g, '<b class="x">×</b>')
        );
    };

    var install_hover_column = function() {

        /* Simulate a mouseover highlight on the current column. */

        var $grid = $('.pile-character-grid');
        var $column = $('<div>', {'class': 'column'}).appendTo($grid);

        $(document).on('mouseenter', '.pile-character-grid b', function() {
            $column.css({
                top: 0,
                bottom: 0,
                left: $(this).position().left,
                right: $(this).parent().width() - $(this).position().left -
                    $(this).outerWidth()
                });
        });
    };

    var install_value_tip = function() {

        var $tip = $('<div class="value-tip">').appendTo('body');

        $(document).on('mouseenter', '.pile-character-grid b', function() {
            var $this = $(this);
            var offset = $this.offset();
            var value = character_values[$this.index() - 2];
            $tip.text(value);
            var hoffset = ($this.outerWidth() - $tip.outerWidth()) / 2;
            $tip.css({
                display: 'block',
                top: offset.top - 32,
                left: offset.left + hoffset
            });
        });

        $(document).on('mouseleave', '.pile-character-grid b', function() {
            $tip.hide();
        });
    };

    var install_click_handlers = function() {

        $(document).on('click', '.pile-character-grid b', function() {
            $(this).toggleClass('x');
        });
        $(document).on('click', '.pile-character-grid span', function() {
            /* TODO: move the bigrow into place */
        });
    };

    var install_expand_button = function() {

        var $button = $('<span>').addClass('expand-button').text('expand ▶');
        var hoffset = $button.width() + 20;

        $(document).on('mouseenter', '.pile-character-grid div', function() {
            $button.appendTo($(this).children().eq(0));
        });

        $(document).on('mouseleave', '.pile-character-grid div', function() {
            $button.remove();
        });
    };

    var split_huge_bigrow = function() {

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

        /* Keep the grid header always in view. */

    };

    return exports;
});
