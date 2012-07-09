define([
    'bridge/jquery'
], function ($) {
    // Constructor
    var Slider = function (container_element, options) {
        this.container_element = container_element;
        this.options = $.extend({}, this.defaults, options);
        this.is_pressed = false;
        this.is_touch = navigator.userAgent.match(
                        /(iPad|iPod|iPhone|Android)/) ? true : false;
        this.bar_left_offset = null;
        this.bar_max_left = null;
        this.bar_min_left = null;
        this.bar_width = null;
        this.number_of_segments = null;
        this.pixels_per_value = null;
        this.thumb_width = null;
        this.value = null;
        this.init();
    };

    // Prototype definition
    Slider.prototype = {
        defaults: {
            bar_left_offset_adjust: 3,
            id: 'gb-slider',
            initial_value: 0,
            maximum: 100,
            minimum: 0,
            orientation: 'horizontal',
            thumb_adjust: 15
        },

        build_slider: function () {
            var slider = $('<div id="' + this.options.id + '">' +
                           '<div class="bar"><div></div></div>' +
                           '<div class="thumb"><div class="label"></div>' +
                           '</div></div>');
            $(this.container_element).append(slider);
        },

        position_for_value: function (value) {
            // Calculate the left position of the slider thumb for a value.
            var position = Math.floor(value * this.pixels_per_value) +
                           this.options.bar_left_offset_adjust;
            return position;
        },

        value_for_position: function (position) {
            // Calculate the value corresponding to a given left position
            // of the slider thumb.
            var thumb_center_position = position + (this.thumb_width / 2);
            var value = Math.floor(thumb_center_position /
                                   this.pixels_per_value);
            return value;
        },

        set_thumb: function (left, thumb) {
            // First if necessary, correct the left position in order to
            // allow pressing on the bar right up to its edges.
            if (left < this.bar_min_left &&
                left >= this.bar_min_left - this.options.thumb_adjust) {

                left = this.bar_min_left;
            }
            else if (left > this.bar_max_left &&
                     left <= this.bar_max_left + this.options.thumb_adjust) {

                left = this.bar_max_left;
            }

            // If the given left position is within the bar, set the thumb
            // there and update its label.
            if (left >= this.bar_min_left && left <= this.bar_max_left) {
                $(thumb).css({'left': left});
                this.set_label(this.value_for_position(left));
            }
        },

        handle_press: function (event) {
            this.is_pressed = true;
            event.preventDefault();   // prevent accidental text selection
            event.stopPropagation();
        },

        handle_move: function (event, thumb) {
            var x = event.pageX;
            var left = x - this.bar_left_offset - (this.thumb_width / 2);
            if (this.is_pressed) {
                this.set_thumb(left, thumb);
                event.stopPropagation();

                if (this.options.on_move &&
                    typeof(this.options.on_move) === 'function') {

                    this.options.on_move();
                }
            }
        },

        handle_release: function () {
            this.is_pressed = false;
        },

        id_selector: function () {
            return '#' + this.options.id;
        },

        set_label: function (value) {
            var label = $(this.container_element).find(this.id_selector() +
                                                       ' .label')[0];
            $(label).html(value);
        },

        init: function () {
            var self = this;
            var id_selector = '#' + this.options.id;

            // Build the slider and bind the event handlers.

            self.build_slider();
            this.value = this.options.initial_value;
            self.set_label(this.value);
            
            var bar = $(this.container_element).find(self.id_selector() +
                                                     ' .bar')[0];
            var offset = $(bar).offset();
            this.bar_left_offset = offset.left;
            this.bar_width = $(bar).width();

            var thumb = $(this.container_element).find(self.id_selector() +
                                                       ' .thumb')[0];
            this.thumb_width = $(thumb).width();

            this.bar_min_left = 0 + this.options.bar_left_offset_adjust;
            this.bar_max_left = this.bar_width - this.thumb_width +
                                this.options.bar_left_offset_adjust;

            this.number_of_segments = this.options.maximum -
                                      this.options.minimum + 1;
            this.pixels_per_value = this.bar_width / this.number_of_segments;

            var left_position = self.position_for_value(this.value);
            self.set_thumb(left_position, thumb);

            if (this.is_touch) {
                $(thumb).bind({
                    'touchstart.Slider': function () {
                        self.handle_press();
                    },
                    'touchmove.Slider': function (event) {
                        event.preventDefault();   // prevent scrolling
                        var original_event = event.originalEvent;
                        self.handle_move(original_event, thumb);
                    },
                    'touchend.Slider': function () {
                        self.handle_release();
                    }
                });
                // No need to support tapping on the slider bar to
                // move the thumb on touch interfaces: iOS does not
                // support this on its native slider control.
            }
            else {
                $(thumb).bind({
                    'mousedown.Slider': function (event) {
                        self.handle_press(event);
                    },
                    'mousemove.Slider': function (event) {
                        event.preventDefault();   // prevent scrolling
                        var original_event = event.originalEvent;
                        self.handle_move(original_event, thumb);
                    },
                    'mouseup.Slider': function () {
                        self.handle_release();
                    }
                });

                $(bar).bind({
                    'mousedown.Slider.bar': function (event) {
                        self.handle_press(event);
                        self.handle_move(event, thumb);
                    },
                    'mouseup.Slider.bar': function () {
                        self.handle_release();
                    }
                });

                $('body').unbind('mousemove.Slider');
                $('body').unbind('mouseup.Slider');

                $('body').bind({
                    'mousemove.Slider': function (event) {
                        self.handle_move(event, thumb);
                    },
                    'mouseup.Slider': function () {
                        self.handle_release();
                    }
                });
            }
        }   // end init()
    };   // end prototype definition

    // Extend jQuery with slider capability.
    $.fn.slider = function (options) {
        new Slider(this, options);
        return this;
    };
});
