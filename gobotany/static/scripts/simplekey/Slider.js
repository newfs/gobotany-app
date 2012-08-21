/*
 * Slider, for integer numeric fields.
 */
define([
    'bridge/jquery',
    'util/slider',
    'simplekey/App3',
    'simplekey/Choice'
], function($, slider, App3, Choice) {

    var Slider = function() {};
    Slider.prototype = new Choice();

    Slider.prototype.init = function(args) {
        this.slider_container_node = null;
        this.horizontal_slider = null;
        Choice.prototype.init.call(this, args);
    };

    /* See the comments on the Choice class, above, to learn about when
       and how these methods are invoked. */

    Slider.clear = function() {
    };

    Slider.dismiss = function() {
        if (this.slider_container_node) {
            $(this.slider_container_node).empty();
        }
        this.horizontal_slider = this.slider_container_node = null;
        this.inherited(arguments);
    };

    Slider._compute_min_and_max = function() {
        var species_vector = App3.filter_controller.compute(this.filter);
        var allowed = this.filter.allowed_ranges(species_vector);
        this.min = allowed[0].min;
        this.max = allowed[allowed.length - 1].max;
    };

    Slider._draw_specifics = function() {
        // values_list?
        this._compute_min_and_max();

        var filter = this.filter;
        var num_values = this.max - this.min + 1;
        var startvalue = Math.ceil(num_values / 2);
        if (filter.value !== null)
            startvalue = filter.get('value');

        var $values_div = $('div.working-area .values');

        $values_div.addClass('multiple').removeClass('numeric').
            html('<label>Select a number between<br>' +
                 this.min + ' and ' +
                 this.max + '</label>');

        this.slider_container_node = $values_div.append('<div></div>');

        this.horizontal_slider = $(this.slider_container_node).slider({
            id: 'slider',
            initial_value: startvalue,
            maximum: this.max,
            minimum: this.min,
            on_move: $.proxy(this, '_value_changed')
        });

        this._value_changed();
    };

    Slider._current_value = function() {
        var slider_label = $('#slider .label')[0];
        var value = $(slider_label).html();
        return value;
    };

    Slider._value_changed = function() {
        /* Disable the apply button when we're on either the default
           value or the value that was previous selected */
        this._compute_min_and_max();

        var $apply_button = $('.apply-btn', this.div);
        var slider_value = this._current_value();
        var filter_value = this.filter.get('value');
        // Allow type coersion in this comparison, since we're
        // comparing text from the filter to a numerical slider value
        if (slider_value == filter_value)
            $apply_button.addClass('disabled');
        else
            $apply_button.removeClass('disabled');
    };

    /* Sliders only have one filter value, so we don't need to compute
       number of taxa for each "choice."  We also don't want to get
       javascript errors from the parent version of this function, so
       just override it with an empty function. */

    Slider._on_filter_change = function() {
    };

    return Slider;
});
