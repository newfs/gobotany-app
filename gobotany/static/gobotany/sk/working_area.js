define([
    'gobotany/utils',
    'dojo/NodeList-html',
    'dijit/form/HorizontalSlider',
    'gobotany/sk/Choice'
], function(utils) {

dojo.provide('gobotany.sk.working_area');

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

/**
 * Return the correct working area class for a given filter.
 *
 * @param {Filter} filter The filter for which you want a working area.
 * @return {Class} The class that will manage this kind of working area.
 */
gobotany.sk.working_area.select_working_area = function(filter) {
    if (filter.value_type == 'TEXT')
        return gobotany.sk.working_area.Choice;
    else if (filter.is_length)
        return gobotany.sk.working_area.Length;
    else
        return gobotany.sk.working_area.Slider;
};


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
        if(this.simple_slider) {
            this.simple_slider.destroy();
        }
        if(this.slide_node) { 
            dojo.query(this.slider_node).orphan();
        }
        this.simple_slider = this.slider_node = null;
        this.inherited(arguments);
    },

    _compute_min_and_max: function() {
        var species_vector = App3.filter_controller.compute(this.filter);
        var allowed = this.filter.allowed_ranges(species_vector);
        this.min = allowed[0].min;
        this.max = allowed[allowed.length - 1].max;
    },

    _draw_specifics: function() {
        // values_list?
        this._compute_min_and_max();

        var filter = this.filter;
        var num_values = this.max - this.min + 1;
        var startvalue = Math.ceil(num_values / 2);
        if (filter.value !== null)
            startvalue = filter.get('value');

        var values_q = dojo.query('div.working-area .values');
        values_q.addClass('multiple').removeClass('numeric').
            html('<label>Select a number between<br>' +
                 this.min + ' and ' +
                 this.max + '</label>');
        this.slider_node = dojo.create('div', null, values_q[0]);
        this.simple_slider = new dijit.form.HorizontalSlider({
            id: 'simple-slider',
            name: 'simple-slider',
            value: startvalue,
            minimum: this.min,
            maximum: this.max,
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
        /* Disable the apply button when we're on either the default
           value or the value that was previous selected */
        this._compute_min_and_max();

        var apply_button = dojo.query('.apply-btn', this.div);
        var slider_value = this._current_value();
        var filter_value = this.filter.get('value');
        // Allow type coersion in this comparison, since we're
        // comparing text from the filter to a numerical slider value
        if (slider_value == filter_value)
            apply_button.addClass('disabled');
        else
            apply_button.removeClass('disabled');

        /* Update the count label. */
        var label = dojo.query('#simple-slider .count');
        var value = this._current_value();
        label.html(value + '');

        /* Position the label atop the slider. */
        var MIN_LEFT_PX = 25;
        var slider_bar = dojo.query('div.dijitSliderBarContainerH')[0];
        var slider_bar_width = dojo.style(slider_bar, 'width');
        var max_left_px = MIN_LEFT_PX + slider_bar_width;
        var filter = this.filter;
        var num_segments = this.max - this.min;
        var slider_length = max_left_px - MIN_LEFT_PX;
        var pixels_per_value = slider_length / num_segments;
        var offset = Math.floor((value - this.min) * pixels_per_value);
        var label_width_correction = 0;
        if (value >= 10) {
            label_width_correction = -4; /* for 2 digits, pull left a bit */
        }
        var left = offset + MIN_LEFT_PX + label_width_correction;
        dojo.style(label[0], 'left', left + 'px');
    },

    /* Sliders only have one filter value, so we don't need to compute
       number of taxa for each "choice."  We also don't want to get
       javascript errors from the parent version of this function, so
       just override it with an empty function. */
    _on_filter_change: function() {
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
    is_metric: true,
    factor: 1.0,
    factormap: {'mm': 1.0, 'cm': 10.0, 'm': 1000.0, 'in': 25.4, 'ft': 304.8},

    clear: function() {
    },

    _draw_specifics: function() {
        var v = dojo.query('div.working-area .values');

        this._set_unit(this.filter.display_units || 'mm');
        this_unit = this.unit;  // for the use of our inner functions
        var value = this.filter.get('value');
        if (value === null)
            value = '';
        else
            value = value / this.factor;

        var radio_for = function(unit) {
            return '<label><input name="units" type="radio" value="' + unit +
                '"' + (unit === this_unit ? ' checked' : '') +
                '>' + unit + '</label>';
        };

        var input_for = function(name, insert_value) {
            return '<input class="' + name + '" name="' + name +
                '" type="text"' +
                (insert_value ? ' value="' + value + '"' : ' disabled') +
                '>';
        };

        v.empty().addClass('numeric').removeClass('multiple').html(
            '<div class="permitted_ranges"></div>' +
            '<div class="current_length"></div>' +

            '<div class="measurement">' +
            'Metric length: ' +
            input_for('measure_metric', this.is_metric) +
            radio_for('mm') +
            radio_for('cm') +
            radio_for('m') +
            '</div>' +

            '<div class="measurement">' +
            'English length: ' +
            input_for('measure_english', ! this.is_metric) +
            radio_for('in') +
            radio_for('ft') +
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

    _parse_value: function(text) {
        var v = parseFloat(text);
        if (isNaN(v))
            return null;
        return v;
    },

    _current_value: function() {
        var selector = this.is_metric ? '[name="measure_metric"]' :
            '[name="measure_english"]';
        var text = dojo.query(selector, this.div).attr('value')[0];
        var v = this._parse_value(text);
        return (v === null) ? null : v * this.factor;
    },

    _set_unit: function(unit) {
        this.unit = unit;
        this.factor = this.factormap[this.unit];
        this.is_metric = /m$/.test(this.unit);
    },

    _unit_changed: function(event) {
        this._set_unit(event.target.value);
        dojo.query('.measure_metric').attr('disabled', ! this.is_metric);
        dojo.query('.measure_english').attr('disabled', this.is_metric);
        this._redraw_permitted_ranges();
        this._measure_changed();
    },

    _measure_changed: function() {
        var mm = this._current_value();
        var mm_old = this._parse_value(this.filter.get('value'));
        var vector = this.filter.taxa_matching(mm);
        vector = _.intersect(vector, this.species_vector);
        var div = dojo.query('.instructions', this.div);
        var apply_button = dojo.query('.apply-btn', this.div);
        if (mm_old === mm) {
            instructions = 'Change the value to narrow your selection to a' +
                ' new set of matching species.';
            apply_button.addClass('disabled');
        } else if (vector.length > 0) {
            instructions = 'Press “Apply” to narrow your selection to the ' +
                vector.length + ' matching species.';
            apply_button.removeClass('disabled');
        } else {
            instructions = '';
            apply_button.addClass('disabled');
        }
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

        var species_vector = App3.filter_controller.compute(this.filter);
        this.species_vector = species_vector;
        this.permitted_ranges = this.filter.allowed_ranges(species_vector);
        this._redraw_permitted_ranges();
        this._measure_changed();
    }
});

});
