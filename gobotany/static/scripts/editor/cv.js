/* Routines to support character-value editor pages.
 *
 * The markup on these pages is deliberately kept very spare because the
 * combination of "remaining-non-monocots" and "habitat" is so large.
 * Even the choice of tag for a click-able boolean value (we use <b>!)
 * reflects an almost superstitious preference for extreme brevity,
 * because every single mis-step in building and maintaining this page
 * tends to plunge it into utter unresponsiveness.
 *
 * "One of these things is not like the other!"  The two lower-pressure
 * pages - the page displaying all characters and values for a whole
 * taxon, and the page displaying length measurements for a pile - are
 * simply generated using Django page templates.  But the page that
 * displays a character's values for every species in a pile includes
 * far too many elements to be rendered in a reasonable amount of time
 * by a template library as slow as Django's, so Django instead injects
 * JSON data into a <script> tag and we build the actual DOM elements
 * here using fast techniques that render even the largest character-
 * value editor page within a second or two.
 *
 * So rendering looks very different depending on which of the three
 * pages is involved.  But once rendered, the exact same JavaScript
 * event handlers can take over, because length-measure rows look
 * different than value-choice rows; but both of them will be the ONLY
 * <div> elements, ever, inside of the character grid:
 *
 * ROW FOR EDITING BOOLEAN CHARACTER VALUES
 *
 *     A class is applied to each value that is checked at the moment.
 *     Note that (fk) that designates species that are only available as
 *     part of the full key.  For characters whose values' friendly
 *     texts can all fit next to each other in the browser, the actual
 *     value names are shown instead of ×'s.
 *
 *     <div>
 *       <i>Carex abscondita (fk)</i>
 *       <b>×</b>
 *       <b class="x">×</b>
 *       <b>×</b>
 *     </div>
 *
 * ROW FOR EDITING A LENGTH CHARACTER VALUE
 *
 *     Lengths are simply presented as a pair of text fields.
 *
 *     <div><i>Carex abscondita (fk)</i>
 *       Min <input value="1.2">
 *       Max <input value="1.8">
 *       mm
 *     </div>
 *
 * VISUAL TAGS
 *
 *     There are also two possible <span> elements that can appear at
 *     the end of either of the above <div>s, depending on the state of
 *     a row:
 *
 *     <span>!</span>
 *        This marks rows with no value specified, so that botanists know
 *        which rows of the table need immediate attention.
 *
 *     <span class="changed">changed</span>
 *        This marks rows that the botanist has edited such that they now
 *        contain different values than they had when the page was loaded.
 *        Further editing of the row might make this tag disappear, if the
 *        editing brings the value back into line with what is currently in
 *        the database.
 */

define([
    'bridge/jquery',
    'bridge/underscore'
], function(
    $, _
) {
    var exports = {};
    var $grid;                  // the grid <div> itself
    var original_values;        // maps row names to vector

    exports.setup = function() {
        $(document).ready(function() {

            $grid = $('.pile-character-grid');

            var data_driven = (typeof window.grid_data !== 'undefined' &&
                               typeof window.character_values !== 'undefined');

            if (data_driven) {
                take_measurements();
                if (!be_verbose)
                    install_expand_button();
                build_grid_from_json();
            } else {
                original_values = scrape_grid($grid);
            }

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

    var verbose_text_of = function(value_name, omit_x) {
        var c = omit_x ? ' ' : '×';
        var name = value_name;
        if (name === 'Connecticut')
            return ' CT ';
        if (name === 'Maine')
            return ' ME ';
        if (name === 'Massachusetts')
            return ' MA ';
        if (name === 'New Hampshire')
            return ' NH ';
        if (name === 'Rhode Island')
            return ' RI ';
        if (name === 'Vermont')
            return ' VT ';
        var name = value_name.replace(' ', ' ');
        return c + ' ' + name + '  ';
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
       in a single post-processing step!  The `grid_data` array is
       already defined, thanks to a <script> tag in the HTML. */

    var build_grid_from_json = function() {

        original_values = {};

        var snippets = [];

        _.each(grid_data, function(item) {
            var merely_a_family_name = (item.length < 2);

            if (merely_a_family_name) {
                var family_name = item[0];
                snippets.push('<h3>');
                snippets.push(family_name);
                snippets.push('</h3>');
                return;
            }
            var scientific_name_fk = item[0];
            var ones_and_zeroes = item[1];

            var scientific_name = scientific_name_fk.replace(' (fk)', '');
            original_values[scientific_name] = ones_and_zeroes;

            snippets.push('<div><i>');
            snippets.push(scientific_name_fk);
            snippets.push('</i>');
            snippets.push(ones_and_zeroes);
            no_values_selected = (ones_and_zeroes.indexOf('1') === -1);
            if (no_values_selected)
                snippets.push('<span>!</span>');
            snippets.push('<span class="char-lit-source">Taxon Def. Lit. Source: <input class="lit-source" /></span>');
            snippets.push('</div>');
        });

        $grid.html(
            snippets.join('')
                .replace(/0/g, '<b>×</b>')
                .replace(/1/g, '<b class="x">×</b>')
        );

        if (be_verbose) {
            for (var i = 0; i < character_values.length; i++) {
                var verbose_text = verbose_text_of(character_values[i], true);
                var selector = 'div b:nth-child(' + (i + 2) + ')';
                $grid.find(selector).text(verbose_text);
            }
        }
    };

    /* Information about a live grid row. */

    var name_of_row = function($row) {
        /* Returns a string like 'Abelmoschus esculentus' or 'Leaf number' */
        var name = $row.attr('data-name');
        if (!name)
            var name = $row.find('i')[0].firstChild.data.replace(' (fk)', '');
        return name;
    };

    var vector_of_row = function($row) {
        /* Returns a string like '10001011...' showing the DOM state. */
        $inputs = $row.find('input.length');
        if ($inputs.length) {
            var vector = [
                float_from($inputs.eq(0).val()),
                float_from($inputs.eq(1).val())
            ];
        } else {
            var vector = _.map($row.find('b'), function(box) {
                return $(box).hasClass('x') ? '1' : '0';
            }).join('');
        }
        return vector;
    };

    var lit_src_of_row = function($row) {
        /* Returns a string like 'Reference, 1999' */
        $input = $row.find('input.lit-source');
        if (!$input.length) {
            return ''
        }
        return $input.val()
    };

    /* Event handler that expects each of our widgets to operate in two
       phases, to avoid triggering multiple WebKit layouts: first each
       event handler is called to do all of the DOM measurements that it
       needs, returning an object of callbacks; then, the callbacks are
       called and should manipulate the DOM without doing any further
       reading.  */

    var install_event_handlers = function() {

        install_species_button_handlers();
        watch_for_value_clicks();
        watch_for_input_edits();
        expand_lit_source_fields();

        $('.save-button').on('click', function() {
            save_vectors();
        });

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

    var watch_for_value_clicks = function() {
        $grid.on('click', 'b', function() {
            var $b = $(this);
            $b.toggleClass('x');
            recompute_changed_tag($b.parent());
        });
    };

    var watch_for_input_edits = function() {
        var $inputs = $grid.find('input');
        $inputs.on('keydown keyup', function() {
            var $input = $(this);
            var v = $input.val();
            var m = v.match(/^ *[0-9]*[.]?[0-9]* *$/);

            $(this).toggleClass('empty', !v);
            $(this).toggleClass('illegal', !m);
            recompute_changed_tag($input.parents('div').eq(0));
        });
        return;
    };

    var install_species_button_handlers = function() {

        $('.all-species-button').on('click', function() {
            $grid.find('div').css('display', '');
        });

        $('.simple-key-button').on('click', function() {
            $grid.find('div').each(function() {
                if ($(this).find('i').text().indexOf('(fk)') !== -1)
                    $(this).css('display', 'none');
            });
        });
    };

    var expand_lit_source_fields = function () {
        var $lit_inputs = $('input.lit-source, input.default-lit-source');
        function expand_on_focus (input) {
            input.on('focus', function () {
                var $input = $(this)
                var value = $input.val();
                var $new_input = $('<textarea wrap="soft" />')
                $new_input.attr('class', $input.attr('class'));
                $input.replaceWith($new_input);
                $new_input.focus();
                // Replace on blur
                $new_input.val(value).blur(function () {
                    $new_input.replaceWith($input);
                    $input.val($new_input.val());
                    // The event handler is detached when the input is
                    // removed from the DOM, re-attach
                    expand_on_focus($input);
                });
            });
        }
        $lit_inputs.each(function () {
            expand_on_focus($(this));
        });
    }

    /* An orange "changed" flag, displayed on the right side of a row,
       that tells the user the row is not in its original state. */

    var recompute_changed_tag = function($row) {

        /* Grabbing .firstChild avoids the "expand" button text. */
        var name = name_of_row($row);
        var old_vector = original_values[name][0];
        var new_vector = vector_of_row($row);
        var old_lit_src = original_values[name][1];
        var new_lit_src = vector_of_row($row);

        if (old_vector == new_vector && old_lit_src == new_lit_src) {
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
        var name = name_of_row($row);
        var old_vector = original_values[name];
        var new_vector = vector_of_row($row);
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
                'vertical-align': - (i % wrap_at + 1) * row_height,
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

    /* Return the character values as they exist in the DOM. */

    var scrape_grid = function($grid) {
        var value_map = {};
        $grid.find('div').not('.column').each(function() {
            var $row = $(this);
            value_map[name_of_row($row)] = [vector_of_row($row),
                                            lit_src_of_row($row)];
        });
        return value_map;
    };

    var save_vectors = function() {
        $('.save-button').addClass('disabled');

        var $changed_divs = $grid.find('.changed_tag').parent();
        var vectors = _.map($changed_divs, function(div) {
            var $row = $(div);
            return [name_of_row($row), vector_of_row($row), lit_src_of_row($row)];
        });
        var def_lit_src = $('input.default-lit-source').val();

        $('<form>', {
            action: '.',
            method: 'POST'
        }).append($('<input>', {
            name: 'new_values',
            value: JSON.stringify(vectors)
        })).append($('<input>', {
            name: 'default_lit_src',
            value: def_lit_src
        })).append(
            $('input[name="csrfmiddlewaretoken"]').clone()
        ).appendTo(
            $('body')
        ).submit();
    };

    /* The next kind of page that belongs to this character-value
       editing suite is the page that lets botanists edit length values,
       and its code is quite simple. */

    var float_from = function(string) {
        return string.trim() ? parseFloat(string) : null;
    };

    return exports;
});
