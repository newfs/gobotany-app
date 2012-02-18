/*
 * Classes that create and maintain the working area.
 *
 * Upon instantiation, a working-area class draws the entire working area
 * for the filter that it has been given, and then un-hides the working
 * area.  Once up and running, it responds to three calls from outside
 * telling it that the outside world has changed.  It is also responsible
 * for handling every click and interaction inside the working area, and
 * for - when appropriate - forwarding the change in the filter state to
 * the outside world.
 *
 * Inputs:
 *
 * clear() - the user has pressed the "x" next to the filter's name in
 *     the sidebar summary, and the filter value should be moved back
 *     to "don't know" if that is not already the value.
 * dismiss() - the filter working area should be dismissed.
 *
 * Outputs:
 *
 * on_dismiss(filter) - called when the user dismisses the working area.
 */

dojo.provide('gobotany.sk.working_area');

dojo.require('dojo.NodeList-html');

/**
 * Return the correct working area class for a given filter.
 *
 * @param {Filter} filter The filter for which you want a working area.
 * @return {Class} The class that will manage this kind of working area.
 */
gobotany.sk.working_area.select_working_area = function(filter) {
    if (filter.value_type == 'TEXT')
        return gobotany.sk.working_area.Choice;
    else if (filter.is_length())
        return gobotany.sk.working_area.Length;
    else
        return gobotany.sk.working_area.Slider;
};

/*
 * The most basic working-area class, which the other versions of the class
 * inherit from and specialize, is the standard multiple-choice selection.
 */

dojo.declare('gobotany.sk.working_area.Choice', null, {

    div_map: null,  // maps choice value -> <input> element
    close_button_connection: null,  // connection from the close button to us

    /* {div, filter, filter_manager, glossarizer, on_dismiss} */
    constructor: function(args) {
        this.div = args.div;
        this.filter = args.filter;
        this.filter_manager = args.filter_manager;
        this.short_name = args.filter.short_name;
        this.glossarize = dojo.hitch(args.glossarizer, 'markup');
        this._draw_basics(args.y);
        this._draw_specifics();
        this.on_dismiss = args.on_dismiss;

        // The set of values we can let the user select can change as
        // they select and deselect other filters on the page.

        dojo.subscribe('/sk/filter/change', this, '_on_filter_change');
        this._on_filter_change();
    },

    /* Events that can be triggered from outside. */

    clear: function() {
        dojo.query('input', this.div_map['']).attr('checked', true);
    },

    dismiss: function(event) {
        if (event) {
            event.preventDefault();
        }

        dojo.disconnect(this.close_button_connection);
        dojo.disconnect(this.apply_button_connection);
        this.close_button_connection = null;
        this.apply_button_connection = null;

        $(this.div).hide();

        $('.option-list li').removeClass('active');

        this.on_dismiss(this.filter);
    },

    /* Draw the working area. */

    _draw_basics: function(y) {
        var d = dojo.query(this.div);
        var f = this.filter;
        var p = function(s) {return s ? '<p>' + s + '</p>' : s}

        // Show the question, hint and Apply button.
        d.query('h4').html(f.question).forEach(this.glossarize);
        d.query('h4').style({display: 'block'});
        d.query('.hint').html(p(f.hint)).forEach(this.glossarize);
        d.query('.info').style({display: 'block'});

        // Display character drawing, if an image is available.
        if (f.image_url) {
            var image_id = this._get_image_id_from_path(f.image_url);
            var dld_html = '<img id="' + image_id +
                '" src="' + f.image_url + '" alt="character illustration">';
            d.query('.dld').html(dld_html).style({display: 'block'});
        } else {
            d.query('.dld').html('').style({display: 'none'});
        }

        // Use jQuery to show the working area with a slide effect.
        $(d).css('top', y + 'px').slideDown('fast');

        // Hook up the Close button.
        var close_button = d.query('.close')[0];
        this.close_button_connection = dojo.connect(
            close_button, 'onclick', dojo.hitch(this, 'dismiss'));

        // Hook up the Apply button.
        var button = dojo.query('.apply-btn', this.div)[0];
        this.apply_button_connection = dojo.connect(
            button, 'onclick', dojo.hitch(this, '_apply_button_clicked'));
    },

    _draw_specifics: function() {
        var CHOICES_PER_ROW = 5;
        var checked = function(cond) {return cond ? ' checked' : ''};
        var f = this.filter;

        var values_q = dojo.query('div.working-area .values');
        values_q.empty().addClass('multiple').removeClass('numeric');

        // Apply a custom sort to the filter values.
        var values = gobotany.utils.clone(f.values);
        values.sort(_compare_filter_choices);

        var choices_div = dojo.create('div', {'class': 'choices'}, values_q[0]);
        var row_div = dojo.create('div', {'class': 'row'}, choices_div);

        // Create a Don't Know radio button item.
        this.div_map = {};
        var item_html = '<div><label><input name="char_name"' +
            checked(f.selected_value === null) +
            ' type="radio" value=""> ' + _format_value() + '</label></div>';
        this.div_map[''] = dojo.place(item_html, row_div);

        // Create radio button items for each character value.
        var choices_count = 1;

        for (i = 0; i < values.length; i++) {
            var v = values[i];

            var item_html = '<label><input name="char_name" type="radio"' +
                checked(f.selected_value === v.choice) +
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
                var row_div = dojo.create(
                    'div', {'class': 'row'}, choices_div);

            choices_count += 1;

            var character_value_div = dojo.create(
                'div', {'innerHTML': item_html}, row_div);
            this.div_map[v.choice] = character_value_div;

            // Once the item is added, add a tooltip for the drawing.
            if (image_path.length > 0) {
                var image_html = '<img id="' + image_id + '" src="' +
                    image_path + '" alt="drawing showing ' +
                    v.friendly_text + '">';
                new dijit.Tooltip({
                    connectId: [image_id],
                    label: image_html, position: ['after', 'above']
                });
            }

            dojo.query('span.label', character_value_div).forEach(
                this.glossarize);
        }

        // Call a method when radio button is clicked.
        var inputs = values_q.query('input');
        for (var i = 0; i < inputs.length; i++)
            dojo.connect(inputs[i], 'onclick',
                         dojo.hitch(this, '_on_choice_change'));

        // Set up the Apply Selection button.
        this._on_choice_change();
    },

    /* How to grab the currently-selected value from the DOM. */

    _current_value: function() {
        var value = dojo.query('input:checked', this.div).attr('value')[0];
        return value || null;
    },

    /* Update whether the "Apply Selection" button is gray or not. */

    _on_choice_change: function(event) {
        var apply_button = dojo.query('.apply-btn', this.div);
        if (this._current_value() === this.filter.selected_value)
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
        var species_vector = this.filter_manager.compute_species_without(
            this.filter.short_name);
        for (var i = 0; i < this.filter.values.length; i++) {
            var v = this.filter.values[i];
            var vector = _.intersect(species_vector, v.species);
            var count_span_q = dojo.query('.count', this.div_map[v.choice]);
            count_span_q.html('(' + vector.length + ')');
            var input_field_q = dojo.query('input', this.div_map[v.choice]);
            if (vector.length === 0)
                input_field_q.attr('disabled', 'disabled');
            else
                input_field_q.attr('disabled', false); // remove the attribute
        }
    },

    /* When the apply button is pressed, we announce a value change
       unless it would bring the number of species to zero. */

    _apply_button_clicked: function(event) {
        dojo.stopEvent(event);
        var apply_button = dojo.query('.apply-btn', this.div);
        apply_button.removeClass('disabled');
        this._apply_filter_value();
        this.dismiss();
    },

    _apply_filter_value: function() {
        var value = this._current_value();
        if (value !== null && this.filter.species_matching(value).length == 0)
            // Refuse to let the number of matching species be driven to zero.
            return;
        this.filter_manager.set_selected_value(
            this.filter.character_short_name, value);
        dojo.publish('/sk/filter/change', [this.filter]);
    }
});

/*
 * Next comes the slider, for integer numeric fields.
 */

dojo.declare('gobotany.sk.working_area.Slider', [
    gobotany.sk.working_area.Choice
], {

    slider_node: null,
    simple_slider: null,

    /* See the comments on the Choice class, above, to learn about when
       and how these methods are invoked. */

    clear: function() {
    },

    dismiss: function() {
        this.simple_slider.destroy();
        dojo.query(this.slider_node).orphan();
        this.simple_slider = this.slider_node = null;
        this.inherited(arguments);
    },

    _draw_specifics: function() {
        // values_list?
        var filter = this.filter;
        var num_values = filter.max - filter.min + 1;
        var startvalue = Math.ceil(num_values / 2);
        if (filter.selected_value !== null)
            startvalue = filter.selected_value;

        var values_q = dojo.query('div.working-area .values');
        values_q.addClass('multiple').removeClass('numeric').
            html('<label>Select a number between<br>' +
                 filter.min + ' and ' +
                 filter.max + '</label>');
        this.slider_node = dojo.create('div', null, values_q[0]);
        this.simple_slider = new dijit.form.HorizontalSlider({
            id: 'simple-slider',
            name: 'simple-slider',
            value: startvalue,
            minimum: filter.min,
            maximum: filter.max,
            discreteValues: num_values,
            intermediateChanges: true,
            showButtons: false,
            onChange: dojo.hitch(this, this._value_changed),
            onMouseUp: dojo.hitch(this, this._value_changed)
        }, this.slider_node);
        dojo.create('div', {
            'class': 'count',
            'innerHTML': startvalue
        }, this.simple_slider.containerNode);
        this._value_changed();
    },

    _current_value: function() {
        return dijit.byId('simple-slider').value;
    },

    _value_changed: function() {
        var value = this._current_value();
        dojo.query('#simple-slider .count').html(value + '');
    }
});

/*
 * Finally, the text box where users can enter lengths.
 */

dojo.declare('gobotany.sk.working_area.Length', [
    gobotany.sk.working_area.Choice
], {
    permitted_ranges: [],  // [{min: n, max: m}, ...] all measured in mm
    species_vector: [],
    unit: 'mm',
    factor: 1.0,

    clear: function() {
    },

    _draw_specifics: function() {
        var v = dojo.query('div.working-area .values');
        v.empty().addClass('numeric').removeClass('multiple').html(
            '<div class="permitted_ranges"></div>' +
            '<div class="current_length"></div>' +

            '<div class="measurement">' +
            'Metric length: ' +
            '<input class="measure_metric" name="measure_metric"' +
            ' type="text" value="">' +
            '<label>' +
            '<input name="units" type="radio" value="mm" checked>mm' +
            '</label>' +
            '<label>' +
            '<input name="units" type="radio" value="cm">cm' +
            '</label>' +
            '<label>' +
            '<input name="units" type="radio" value="m">m' +
            '</label>' +
            '</div>' +

            '<div class="measurement">' +
            'English length: ' +
            '<input class="measure_english" name="measure_english" ' +
            'type="text" value="" disabled>' +
            '<label>' +
            '<input name="units" type="radio" value="in">in' +
            '</label>' +
            '<label>' +
            '<input name="units" type="radio" value="ft">ft' +
            '</label>' +
            '</div>' +

            '<div class="instructions">' +
            '</div>'
        );
        v.query('[name="units"]').connect('onchange', this, '_unit_changed');
        v.query('[type="text"]').connect('onchange', this, '_measure_changed');
        v.query('[type="text"]').connect('onkeyup', this, '_key_pressed');
    },

    _key_pressed: function(event) {
        if (event.keyCode == 10 || event.keyCode == 13)
            this._apply_filter_value();
        else
            this._measure_changed();
    },

    _current_value: function() {
        var selector = this.is_english ? '[name="measure_english"]' :
            '[name="measure_metric"]';
        var text = dojo.query(selector, this.div).attr('value')[0];
        var mm = parseFloat(text) * this.factor;
        return isNaN(mm) ? null : mm;
    },

    _unit_changed: function(event) {
        this.unit = event.target.value;
        this.factor = ({'mm': 1.0, 'cm': 10.0, 'm': 1000.0,
                        'in': 25.4, 'ft': 304.8})[this.unit];
        this.is_english = (this.unit == 'in' || this.unit == 'ft');
        dojo.query('.measure_metric').attr('disabled', this.is_english);
        dojo.query('.measure_english').attr('disabled', ! this.is_english);
        this._redraw_permitted_ranges();
        this._measure_changed();
    },

    _measure_changed: function() {
        var mm = this._current_value();
        var vector = this.filter.species_matching(mm);
        vector = _.intersect(vector, this.species_vector);
        var div = dojo.query('.instructions', this.div);
        if (vector.length > 0)
            instructions = 'Press “Apply” to narrow your selection to the ' +
                vector.length + ' matching species.';
        else
            instructions = '';
        div.html(instructions);

        // Stash a hint about how the sidebar should display our value.
        this.filter.display_units = this.unit;
    },

    _redraw_permitted_ranges: function() {
        var p = 'Please enter a measurement in the range ';
        var truncate = function(value, precision) {
            var power = Math.pow(10, precision || 0);
            return String(Math.round(value * power) / power);
        };
        for (var i = 0; i < this.permitted_ranges.length; i++) {
            var pr = this.permitted_ranges[i];
            if (i) p += ' or ';
            p += truncate(pr.min / this.factor, 2) + '&nbsp;' + this.unit +
                '&nbsp;–&nbsp;' +  // en-dash for numeric ranges
                truncate(pr.max / this.factor, 2) + '&nbsp;' + this.unit;
        }
        dojo.query('.permitted_ranges', this.div).html(p);
    },

    _on_filter_change: function() {
        // A filter somewhere on the page changed, so we might need to
        // adjust our statement about the number of species matched by
        // the value in our input field.

        var species_vector = this.filter_manager.compute_species_without(
            this.filter.short_name);
        this.species_vector = species_vector;
        this.permitted_ranges = this.filter.allowed_ranges(species_vector);
        this._redraw_permitted_ranges();
        this._measure_changed();
    }
});

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
