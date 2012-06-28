/*
 * The most basic working-area class, which the other versions of the class
 * inherit from and specialize, is the standard multiple-choice selection.
 */
define([
    'dojo/_base/declare',
    'dojo/_base/connect',
    'dojo/_base/lang',
    'dojo/_base/event',
    'dojo/query',
    'dojo/dom-construct',
    'dojo/NodeList-dom',
    'dojo/NodeList-html',
    'dojo/on',
    'bridge/jquery',
    'util/tooltip',
    'bridge/underscore',
    'gobotany/utils',
    'simplekey/glossarize',
    'simplekey/App3'
], function(declare, connect, lang, event, query, domConstruct, nodeListDom,
    nodeListHtml, on, $, tooltip, _, utils, glossarize, App3) {

/*
 * Helper functions
 */

/* Generate a human-readable representation of a value.
 */
var _format_value = function(v) {
    return v === undefined ? "don't know" :
        v.friendly_text ? v.friendly_text :
        v.choice === 'NA' ? "doesn't apply" :
        v.choice ? v.choice : "don't know";
};

/* Order filter choices for display.
 */
var _compare_filter_choices = function(a, b) {

    var friendly_text_a = a.friendly_text.toLowerCase();
    var friendly_text_b = b.friendly_text.toLowerCase();
    var choice_a = a.choice.toLowerCase();
    var choice_b = b.choice.toLowerCase();

    // If both are a number or begin with one, sort numerically.

    var int_friendly_text_a = parseInt(friendly_text_a, 10);
    var int_friendly_text_b = parseInt(friendly_text_b, 10);
    if (!isNaN(int_friendly_text_a) && !isNaN(int_friendly_text_b)) {
        return int_friendly_text_a - int_friendly_text_b;
    }
    var int_choice_a = parseInt(choice_a, 10);
    var int_choice_b = parseInt(choice_b, 10);
    if (!isNaN(int_choice_a) && !isNaN(int_choice_b)) {
        return int_choice_a - int_choice_b;
    }

    // Otherwise, sort alphabetically.

    // Exception: always make Doesn't Apply (NA) last.
    if (choice_a === 'na') return 1;
    if (choice_b === 'na') return -1;

    // If friendly text is present, sort using it.
    if (friendly_text_a < friendly_text_b) return -1;
    if (friendly_text_a > friendly_text_b) return 1;

    // If there is no friendly text, sort using the choices instead.
    if (choice_a < choice_b) return -1;
    if (choice_a > choice_b) return 1;

    return 0; // default value (no sort)
};

return declare('gobotany.sk.working_area.Choice', null, {

    div_map: null,  // maps choice value -> <input> element
    close_button_signal: null,  // connection from the close button to us

    /* {div, filter, on_dismiss} */
    constructor: function(args) {
        this.div = args.div;
        this.filter = args.filter;
        this._draw_basics(args.y);
        this._draw_specifics();
        this.on_dismiss = args.on_dismiss;

        // The set of values we can let the user select can change as
        // they select and deselect other filters on the page.

        connect.subscribe('/sk/filter/change', this, '_on_filter_change');
        this._on_filter_change();
    },

    /* Events that can be triggered from outside. */

    clear: function() {
        query('input', this.div_map['']).attr('checked', true);
    },

    dismiss: function(e) {
        if (e) {
            e.preventDefault();
        }

        this.close_button_signal.remove();
        this.apply_button_signal.remove();
        this.close_button_signal = null;
        this.apply_button_signal = null;

        $(this.div).hide();

        $('.option-list li').removeClass('active');

        this.on_dismiss(this.filter);
    },

    /* Draw the working area. */

    _draw_basics: function(y) {
        var d = query(this.div);
        var f = this.filter;
        var p = function(s) {return s ? '<p>' + s + '</p>' : s}

        // Show the question, hint and Apply button.
        glossarize($('h4').html(f.info.question));
        $('h4').css('display', 'block');
        glossarize($('.hint').html(p(f.info.hint)));
        $('.info').css('display', 'block');

        // Display character drawing, if an image is available.
        if (f.info.image_url) {
            var image_id = this._get_image_id_from_path(f.info.image_url);
            var dld_html = '<img id="' + image_id +
                '" src="' + f.info.image_url +
                '" alt="character illustration">';
            d.query('.dld').html(dld_html).style({display: 'block'});
        } else {
            d.query('.dld').html('').style({display: 'none'});
        }

        // Use jQuery to show the working area with a slide effect.
        $(d).css('top', y + 'px').slideDown('fast');

        // Hook up the Close button.
        var close_button = d.query('.close')[0];
        this.close_button_signal = on(
            close_button, 'click', lang.hitch(this, 'dismiss'));

        // Hook up the Apply button.
        var button = query('.apply-btn', this.div)[0];
        this.apply_button_signal = on(
            button, 'click', lang.hitch(this, '_apply_button_clicked'));
    },

    _draw_specifics: function() {
        var CHOICES_PER_ROW = 5;
        var checked = function(cond) {return cond ? ' checked' : ''};
        var f = this.filter;

        var values_q = query('div.working-area .values');
        values_q.empty().addClass('multiple').removeClass('numeric');

        // Apply a custom sort to the filter values.
        var values = utils.clone(f.values);
        values.sort(_compare_filter_choices);

        var choices_div = domConstruct.create('div', {'class': 'choices'}, values_q[0]);
        var row_div = domConstruct.create('div', {'class': 'row'}, choices_div);

        // Create a Don't Know radio button item.
        this.div_map = {};
        var item_html = '<div><label><input name="char_name"' +
            checked(f.value === null) +
            ' type="radio" value=""> ' + _format_value() + '</label></div>';
        this.div_map[''] = domConstruct.place(item_html, row_div);

        // Create radio button items for each character value.
        var choices_count = 1;

        for (i = 0; i < values.length; i++) {
            var v = values[i];

            var item_html = '<label><input name="char_name" type="radio"' +
                checked(f.value === v.choice) +
                ' value="' + v.choice + '">';

            // Add a drawing image if present.
            var image_path = v.image_url;
            if (image_path.length > 0) {
                var image_id = this._get_image_id_from_path(image_path);
                item_html += '<img id="' + image_id +
                    '" src="' + image_path + '" alt="drawing ' +
                    'showing ' + v.friendly_text + '"><br>';
            }

            item_html += ' <span class="label">' + _format_value(v) +
                '</span> <span class="count">(n)</span>' +
                '</label>';

            // Start a new row, if necessary, to fit this choice.
            if (choices_count % CHOICES_PER_ROW === 0)
                var row_div = domConstruct.create(
                    'div', {'class': 'row'}, choices_div);

            choices_count += 1;

            var character_value_div = domConstruct.create(
                'div', {'innerHTML': item_html}, row_div);
            this.div_map[v.choice] = character_value_div;

            // Once the item is added, add a tooltip for the drawing.
            if (image_path.length > 0) {
                var image_html = '<img class="char-value-larger" id="' +
                    image_id + '" src="' + image_path +
                    '" alt="drawing showing ' + v.friendly_text + '">';
                $('#' + image_id).tooltip({
                    content: image_html,
                    width: 'auto'
                });
            }

            glossarize($('span.label', character_value_div));
        }

        // Call a method when radio button is clicked.
        var inputs = values_q.query('input');
        for (var i = 0; i < inputs.length; i++)
            on(inputs[i], 'click', lang.hitch(this, '_on_choice_change'));

        // Set up the Apply Selection button.
        this._on_choice_change();
    },

    /* How to grab the currently-selected value from the DOM. */

    _current_value: function() {
        var value = query('input:checked', this.div).attr('value')[0];
        return value || null;
    },

    /* Update whether the "Apply Selection" button is gray or not. */

    _on_choice_change: function(e) {
        var apply_button = query('.apply-btn', this.div);
        if (this._current_value() === this.filter.value)
            apply_button.addClass('disabled');
        else
            apply_button.removeClass('disabled');
    },

    /* Get a value suitable for use as an image element id from the
       image filename found in the image path. */

    _get_image_id_from_path: function(image_path) {
        var last_slash_index = image_path.lastIndexOf('/');
        var dot_index = image_path.indexOf('.', last_slash_index);
        var image_id = image_path.substring(last_slash_index + 1, dot_index);
        return image_id;
    },

    /* When the set of selected filters changes, we need to recompute
       how many species would remain if each of our possible filter
       values were applied. */
    _on_filter_change: function() {
        var other_taxa = App3.filter_controller.compute(this.filter);
        var div_map = this.div_map;

        _.map(this.filter.values, function(value) {

            // How many taxa would be left if this value were chosen?
            var num_taxa = _.intersect(value.taxa, other_taxa).length;

            // Draw it accordingly.
            var div = div_map[value.choice];
            var count_span_q = query('.count', div);
            count_span_q.html('(' + num_taxa + ')');
            var input_field_q = query('input', div);
            if (num_taxa === 0) {
                $(div).addClass('disabled');
                input_field_q.attr('disabled', 'disabled');
            } else {
                $(div).removeClass('disabled');
                input_field_q.attr('disabled', false); // remove the attribute
            }
        });
    },

    /* When the apply button is pressed, we announce a value change
       unless it would bring the number of species to zero. */

    _apply_button_clicked: function(e) {
        event.stop(e);
        var apply_button = $('.apply-btn');
        if (apply_button.hasClass('disabled'))
            return;
        apply_button.removeClass('disabled');
        this._apply_filter_value();
        this.dismiss();
    },

    _apply_filter_value: function() {
        var value = this._current_value();
        if (value !== null && this.filter.taxa_matching(value).length == 0)
            // Refuse to let the number of matching taxa be driven to zero.
            return;
        this.filter.set('value', value);
    }
});
});
