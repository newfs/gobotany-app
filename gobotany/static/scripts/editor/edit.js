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
            install_expand_button();
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

        $grid.on('click', 'b', function() {
            $(this).toggleClass('x');
        });
    };

    /* Simulate a mouseover highlight of the current column. */

    var install_hover_column = function() {

        var $grid = $('.pile-character-grid');
        var $column = $('<div>', {'class': 'column'}).appendTo($grid);

        $grid.on('mouseenter', 'b', function() {
            $column.css({
                top: 0,
                bottom: 0,
                left: $(this).position().left,
                right: $(this).parent().width() - $(this).position().left -
                    $(this).outerWidth(true)
                });
        });
    };

    /* Mousing over a "x" should display a lightweight tooltip naming
       the value controlled by that "x".  For fun, we also highlight the
       same name in an expanded row, if one happens to be expanded. */

    var install_value_tip = function() {

        var $grid = $('.pile-character-grid');
        var $tip = $('<div class="value-tip">').appendTo('body');

        $grid.on('mouseenter', 'b', function() {
            var $this = $(this);
            var $row = $this.parent();
            var index = $this.index() - 1;

            $grid.find('div.expanded b').eq(index).addClass('highlight');

            if ($row.hasClass('expanded'))
                return;

            var offset = $this.offset();
            var value = character_values[index];

            $tip.text(value);
            var hoffset = ($this.outerWidth() - $tip.outerWidth()) / 2;

            $tip.css({
                display: 'block',
                top: offset.top - 32,
                left: offset.left + hoffset
            });
        });

        $grid.on('mouseleave', 'b', function() {
            $tip.hide();
            $grid.find('div.expanded').find('b').removeClass('highlight');
        });
    };

    var install_expand_button = function() {

        var $button = $('<span>').addClass('expand-button').text('expand ▶');
        var $mouse_row;
        var $expanded_row = null;

        $('.pile-character-grid').on('mouseenter', 'div', function() {
            $mouse_row = $(this);
            $button.appendTo($mouse_row.children().eq(0));
        });

        $('.pile-character-grid').on('mouseleave', 'div', function() {
            $button.detach();
        });

        $button.on('click', function() {
            if ($expanded_row !== null) {
                unexpand_row($expanded_row);
                $button.text('expand ▶');
            }
            if (! $mouse_row.is($expanded_row)) {
                expand_row($mouse_row);
                $expanded_row = $mouse_row;
                $button.text('expand ▼');
            } else {
                $expanded_row = null;
            }
        });
    };

    var expand_row = function($row) {

        $row.addClass('expanded');

        var $boxes = $row.find('b');
        var xwidth = $boxes.width();
        var height = $row.height();
        var ywrap = height * 14;

        for (i = 0; i < $boxes.length; i++) {
            var $box = $boxes.eq(i);
            $box.css('vertical-align', - (height * i % ywrap));
            $box.text($box.text() + ' ' + character_values[i]);
            $box.css('margin-right', xwidth - $box.width());
        }
    };

    var unexpand_row = function($row) {

        $row.removeClass('expanded');

        var $boxes = $row.find('b');
        $boxes.text('×');
        $boxes.css({
            'position': '',
            'vertical-align': '',
            'margin-right': ''
        });

    };

    return exports;
});
