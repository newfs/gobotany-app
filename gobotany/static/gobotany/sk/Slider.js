/*
 * Slider, for integer numeric fields.
 */
define([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dojo/query',
    'dojo/NodeList-dom',
    'dojo/NodeList-html',
    'dojo/dom-construct',
    'dojo/dom-style',
    'dijit/registry',
    'dijit/form/HorizontalSlider',
    'gobotany/sk/Choice',
    'simplekey/App3'
], function(declare, lang, query, nodeListDom, nodeListHtml, domConstruct, 
    domStyle, registry, HorizontalSlider, Choice, App3) {

return declare('gobotany.sk.working_area.Slider', [
    Choice
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
            query(this.slider_node).orphan();
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

        var values_q = query('div.working-area .values');
        values_q.addClass('multiple').removeClass('numeric').
            html('<label>Select a number between<br>' +
                 this.min + ' and ' +
                 this.max + '</label>');
        this.slider_node = domConstruct.create('div', null, values_q[0]);
        this.simple_slider = new HorizontalSlider({
            id: 'simple-slider',
            name: 'simple-slider',
            value: startvalue,
            minimum: this.min,
            maximum: this.max,
            discreteValues: num_values,
            intermediateChanges: true,
            showButtons: false,
            onChange: lang.hitch(this, this._value_changed),
            onMouseUp: lang.hitch(this, this._value_changed)
        }, this.slider_node);
        domConstruct.create('div', {
            'class': 'count',
            'innerHTML': startvalue
        }, this.simple_slider.containerNode);
        this._value_changed();
    },

    _current_value: function() {
        return registry.byId('simple-slider').value;
    },

    _value_changed: function() {
        /* Disable the apply button when we're on either the default
           value or the value that was previous selected */
        this._compute_min_and_max();

        var apply_button = query('.apply-btn', this.div);
        var slider_value = this._current_value();
        var filter_value = this.filter.get('value');
        // Allow type coersion in this comparison, since we're
        // comparing text from the filter to a numerical slider value
        if (slider_value == filter_value)
            apply_button.addClass('disabled');
        else
            apply_button.removeClass('disabled');

        /* Update the count label. */
        var label = query('#simple-slider .count');
        var value = this._current_value();
        label.html(value + '');

        /* Position the label atop the slider. */
        var MIN_LEFT_PX = 25;
        var slider_bar = query('div.dijitSliderBarContainerH')[0];
        var slider_bar_width = domStyle.get(slider_bar, 'width');
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
        domStyle.set(label[0], 'left', left + 'px');
    },

    /* Sliders only have one filter value, so we don't need to compute
       number of taxa for each "choice."  We also don't want to get
       javascript errors from the parent version of this function, so
       just override it with an empty function. */
    _on_filter_change: function() {
    }

});

});

