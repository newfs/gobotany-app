/* Routines to support editor pages. */

define([
    'bridge/jquery',
    'bridge/underscore',
    'editor/floatingtableheader'
], function(
    $, _
) {
    var exports = {};
    var $grid;                  // the grid <div> itself
    var taxon_value_vectors;    // maps scientific name to vector

    exports.setup_pile_character_page = function() {
        $(document).ready(function() {
            $grid = $('.pile-character-grid');
            take_measurements();
            if (!be_verbose)
                install_expand_button();
            build_grid_from_json();
            install_event_handlers();
        });
    };

    /* Note that take_measurements() is called before the grid is built,
       since operations like .width() that trigger WebKit layout become
       extremely expensive once the grid is in place */

    var be_verbose;             // put value name next to ×
    var row_height;             // height of a standard row
    var x_width;                // width of box containing an ×
    var value_widths;           // width of formatted value texts

    var verbose_text_of = function(value_name) {
        return '× ' + value_name.replace(' ', ' ') + ' ';
    };

    var take_measurements = function() {

        var $row = $('<div>').append($('<i>').text('Species')).appendTo($grid);
        var $b = $('<b>').text('×').appendTo($row);
        row_height = $row.height();
        x_width = $b.outerWidth();
        $b.remove();

        /* Do we have room to include value names inline, and still
           leave as much room on the right side of the grid as species
           names take up on the left? */

        _.each(character_values, function(name) {
            $b = $('<b>').text(verbose_text_of(name)).appendTo($row);
        });
        var space_open = $(window).width() - $b.position().left - $b.width();
        var space_desired = $row.find('i').width();

        be_verbose = (space_open >= space_desired);
        value_widths = _.map($row.find('b'), function(b) {
            return $(b).outerWidth();
        });
    };

    /* To display the /edit/cv/remaining-non-monocots/habitat/ page
       efficiently, we need to be very fast; this simple string
       concatenation seems to do quite well.  Note especially that we
       turn the vector of ones and zeroes into lightweight check boxes
       in a single post-processing step! */

    var build_grid_from_json = function() {

        taxon_value_vectors = {};

        var snippets = [];

        _.each(grid_data, function(item) {
            if (item.length < 2) {
                var family_name = item[0];
                snippets.push('<h3>');
                snippets.push(family_name);
                snippets.push('</h3>');
                return;
            }
            var scientific_name = item[0];
            var ones_and_zeroes = item[1];

            taxon_value_vectors[scientific_name] = ones_and_zeroes;

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

        if (be_verbose) {
            for (var i = 0; i < character_values.length; i++) {
                var verbose_text = verbose_text_of(character_values[i]);
                var selector = 'div b:nth-child(' + (i + 2) + ')';
                $grid.find(selector).text(verbose_text);
            }
        }

        $grid.on('click', 'b', function() {
            var $b = $(this);
            $b.toggleClass('x');
            recompute_changed_tag($b);
        });
    };

    /* Information about a live grid row. */

    var scientific_name_of = function($row) {
        /* Returns a string like 'Abelmoschus esculentus' */
        return $row.find('i')[0].firstChild.data;
    };

    var vector_of = function($row) {
        /* Returns a string like '10001011...' */
        return _.map($row.find('b'), function(box) {
            return $(box).hasClass('x') ? '1' : '0';
        }).join('');
    };

    /* Event handler that expects each of our widgets to operate in two
       phases, to avoid triggering multiple WebKit layouts: first each
       event handler is called to do all of the DOM measurements that it
       needs, returning an object of callbacks; then, the callbacks are
       called and should manipulate the DOM without doing any further
       reading.  */

    var install_event_handlers = function() {

        $grid.on('mouseenter', '.changed_tag', function() {
            add_change_borders($(this).parent());
        });

        $grid.on('mouseleave', '.changed_tag', function() {
            remove_change_borders($(this).parent());
        });

        if (be_verbose)
            return;             // then nothing from here down is relevant

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

    /* An orange "changed" flag, displayed on the right side of a row,
       that tells the user the row is not in its original state. */

    var recompute_changed_tag = function($box) {

        /* Grabbing .firstChild avoids the "expand" button text. */
        var $row = $box.parent();
        var taxon_name = scientific_name_of($row);
        var old_vector = taxon_value_vectors[taxon_name];
        var new_vector = vector_of($row);

        if (old_vector == new_vector) {
            $row.find('.changed_tag').remove();
        } else {
            if ($row.find('.changed_tag').length === 0) {
                $row.append($('<span>', {
                    'class': 'changed_tag',
                    'text': 'changed'
                }));
            }
        }
    };

    /* Mousing over a "changed" tag lets you see the changes. */

    var add_change_borders = function($row) {
        var taxon_name = scientific_name_of($row);
        var old_vector = taxon_value_vectors[taxon_name];
        var new_vector = vector_of($row);
        var $boxes = $row.find('b');

        $boxes.each(function(i) {
            if (old_vector[i] !== new_vector[i])
                $(this).addClass('changed');
        });
    }
    var remove_change_borders = function($row) {
        $row.find('.changed').removeClass('changed');
    }

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
                    width: x_width
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
            $tips.css('display', '');
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
            $button.appendTo($mouse_row.find(':first-child'));
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
                $expanded_row = $mouse_row;
                expand_row($mouse_row);
                $button.text('expand ▼');
            } else {
                $expanded_row = null;
            }
        });
    };

    var expand_row = function($row) {

        $row.addClass('expanded');

        var $boxes = $row.find('b');
        var box_widths = [];
        var wrap_at = 14;

        _.each($boxes, function(box, i) {
            $(box).text(verbose_text_of(character_values[i])).css({
                'vertical-align': - (i % wrap_at) * row_height,
                'margin-right': x_width - value_widths[i]
            });
        });
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
