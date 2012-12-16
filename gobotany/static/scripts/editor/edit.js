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
            take_measurements();
            install_expand_button();
            build_grid_from_json();
            install_event_handlers();
        });
    };

    /* Note that take_measurements() is called before the grid is built,
       since operations like .width() that trigger WebKit layout become
       extremely expensive once the grid is in place */

    var $grid;                  // the grid <div> itself

    var first_box_position;     // upper left <b>×</b> element
    var typical_box_width;      // <b>×</b> element width

    var $value_tips;            // value_str tooltips
    var value_tip_widths;

    var take_measurements = function() {
        $grid = $('.pile-character-grid');

        var $box = $grid.find('div b');
        first_box_position = $box.position();
        typical_box_width = $box.outerWidth();

        $value_tips = $('.value-tips div');
        value_tip_widths = _.map($value_tips, function(tip) {
            return $(tip).width();
        });
    };

    /* To display the /edit/cv/remaining-non-monocots/habitat/ page
       efficiently, we need to be very fast; this simple string
       concatenation seems to do quite well.  Note especially that we
       turn the vector of ones and zeroes into lightweight check boxes
       in a single post-processing step! */

    var build_grid_from_json = function() {

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

    /* Event handler that expects each of our widget to operate in two
       phases, to avoid triggering multiple WebKit layouts: first each
       event handler is called to do all of the DOM measurements that it
       needs, returning an object of callbacks; then, the callbacks are
       called and should manipulate the DOM without doing any further
       reading.  */

    var install_event_handlers = function() {
        var hovercolumn_functions = hovercolumn_setup();
        var valuetip_functions = valuetip_setup();

        $grid.on('mouseenter', 'b', function() {
            var $b = $(this);
            var h_dom_update = hovercolumn_functions.mouseenter($b);
            var v_dom_update = valuetip_functions.mouseenter($b);

            h_dom_update();
            v_dom_update();
        });

        $grid.on('mouseleave', 'b', function() {
            var $b = $(this);
            valuetip_functions.mouseleave($b);
        });
    };

    /* Simulate a mouseover highlight of the current column. */

    var hovercolumn_setup = function() {
        $column = $('<div>', {'class': 'column'}).appendTo($grid);

        var mouseenter = function($b) {
            var left_px = $b.position().left;

            return function update_dom() {
                $column.css({
                    top: 0,
                    bottom: 0,
                    left: left_px,
                    width: typical_box_width
                });
            };
        };

        return {mouseenter: mouseenter};
    };

    /* Mousing over a "x" should display a lightweight tooltip naming
       the value controlled by that "x".  For fun, we also highlight the
       same name in an expanded row, if one happens to be expanded. */

    var valuetip_setup = function() {
        var $tips = $('.value-tips div');
        var $tip;

        var mouseenter = function($b) {
            var index = $b.index() - 1;
            var $row = $b.parent();
            var is_valuetip_needed = ! $row.is($expanded_row);

            if (is_valuetip_needed) {
                $tip = $tips.eq(index);
                var boffset = $b.offset();
                var hleft = ($b.outerWidth() - $tip.outerWidth()) / 2;
            }

            return function update_dom() {
                if ($expanded_row !== null)
                    $expanded_row.find('b').eq(index).addClass('highlight');

                if (is_valuetip_needed) {
                    $tip.css({
                        display: 'block',
                        top: boffset.top - 32,
                        left: boffset.left + hleft
                    });
                }
            };
        };

        var mouseleave = function($b) {
            $tip.css('display', '');
            if ($expanded_row !== null)
                $expanded_row.find('b').removeClass('highlight');
        };

        return {mouseenter: mouseenter, mouseleave: mouseleave};
    };

    /* Let the user expand a row to see all the values explicitly. */

    var $expanded_row = null;

    var install_expand_button = function() {

        var $button = $('<span>').addClass('expand-button').text('expand ▶');
        var $mouse_row;

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
        var wrap_at = 14;

        for (i = 0; i < $boxes.length; i++) {
            var $box = $boxes.eq(i);
            $box.css('vertical-align', - (i % wrap_at) * height);
            $box.text($box.text() + ' ' + character_values[i]);
            $box.css('margin-right', xwidth - $box.width());
        }
    };

    var unexpand_row = function($row) {

        $row.removeClass('expanded');

        var $boxes = $row.find('b');
        $boxes.text('×');
        $boxes.css({
            'vertical-align': '',
            'margin-right': ''
        });

    };

    return exports;
});
