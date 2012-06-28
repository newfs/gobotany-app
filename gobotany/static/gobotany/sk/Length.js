/*
 * Finally, the text box where users can enter lengths.
 */
define([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dojo/query',
    'dojo/NodeList-dom',
    'dojo/NodeList-html',
    'bridge/underscore',
    'gobotany/sk/Choice',
    'simplekey/App3'
], function(declare, lang, query, nodeListDom, nodeListHtml, _, Choice, App3) {

return declare('gobotany.sk.working_area.Length', [
    Choice
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
        var v = query('div.working-area .values');

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
        v.query('[name="units"]').on('change', lang.hitch(this, '_unit_changed'));
        v.query('[type="text"]').on('change', lang.hitch(this, '_measure_changed'));
        v.query('[type="text"]').on('keyup', lang.hitch(this, '_key_pressed'));
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
        var text = query(selector, this.div).attr('value')[0];
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
        query('.measure_metric').attr('disabled', ! this.is_metric);
        query('.measure_english').attr('disabled', this.is_metric);
        this._redraw_permitted_ranges();
        this._measure_changed();
    },

    _measure_changed: function() {
        var mm = this._current_value();
        var mm_old = this._parse_value(this.filter.get('value'));
        var vector = this.filter.taxa_matching(mm);
        vector = _.intersect(vector, this.species_vector);
        var div = query('.instructions', this.div);
        var apply_button = query('.apply-btn', this.div);
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
        query('.permitted_ranges', this.div).html(p);
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

