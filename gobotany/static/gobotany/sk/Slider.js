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
    'util/slider',
    'gobotany/sk/Choice',
    'simplekey/App3'
], function(declare, lang, query, nodeListDom, nodeListHtml, domConstruct, 
    domStyle, slider, Choice, App3) {

return declare('gobotany.sk.working_area.Slider', [
    Choice
], {
    slider_container_node: null,
    horizontal_slider: null,

    /* See the comments on the Choice class, above, to learn about when
       and how these methods are invoked. */

    clear: function() {
    },

    dismiss: function() {
        if (this.slider_container_node) {
            $(this.slider_container_node).empty();
        }
        this.horizontal_slider = this.slider_container_node = null;
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

        var values_div = $('.working-area .info .values')[0];
        this.slider_container_node = $(values_div).append('<div></div>');        
        this.horizontal_slider = $(this.slider_container_node).slider({
            id: 'slider',
            initial_value: startvalue,
            maximum: this.max,
            minimum: this.min,
            on_move: lang.hitch(this, this._value_changed)
        });
        
        this._value_changed();
    },

    _current_value: function() {
        var slider_label = $('#slider .label')[0];
        var value = $(slider_label).html();
        return value;
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
    },

    /* Sliders only have one filter value, so we don't need to compute
       number of taxa for each "choice."  We also don't want to get
       javascript errors from the parent version of this function, so
       just override it with an empty function. */
    _on_filter_change: function() {
    }

});

});

