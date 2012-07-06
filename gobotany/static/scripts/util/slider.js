define([
    'bridge/jquery'
], function ($) {
    // Constructor
    var Slider = function (container_element, options) {
        this.container_element = container_element;
        this.options = $.extend({}, this.defaults, options);
        this.is_down = false;
        this.is_touch = navigator.userAgent.match(
                        /(iPad|iPod|iPhone|Android)/) ? true : false;
        this.bar_left_offset = null;
        this.bar_width = null;
        this.thumb_width = null;
        this.init();
    };

    // Prototype definition
    Slider.prototype = {
        defaults: {
            bar_left_offset_adjust: 3,
            id: 'gb-slider',
            maximum: 100,
            minimum: 0,
            orientation: 'horizontal',
            value: null
        },

        build_slider: function () {
            var slider = $('<div id="' + this.options.id + '">' +
                           '<div class="bar"><div></div></div>' +
                           '<div class="thumb"><div class="label"></div>' +
                           '</div></div>');
            $(this.container_element).append(slider);
        },

        handle_press: function (event) {
            this.is_down = true;
            //console.log('handle_press - is_down:', this.is_down);
            event.preventDefault();   // prevent accidental text selection
            event.stopPropagation();
        },

        handle_move: function (event, thumb) {
            //console.log('handle_move - is_down: ' + this.is_down);
            var x = event.pageX;
            var client_x = event.clientX;
            var left = x - this.bar_left_offset - (this.thumb_width / 2);
            if (this.is_down) {
                console.log(' pageX: ' + x + ' clientX:' + client_x +
                            ' left: ' + left);
                // If the place where the user is pressing is within the
                // bar, position the thumb accordingly. 
                if ((left >= 0 + this.options.bar_left_offset_adjust) &&
                    (left <= this.bar_width - this.thumb_width +
                     this.options.bar_left_offset_adjust)) {

                    $(thumb).css({'left': left});
                }
                event.stopPropagation();
            }
        },

        handle_release: function () {
            this.is_down = false;
            //console.log('handle_release - is_down:', this.is_down);
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

            console.log('Slider init(): min: ' + this.options.minimum +
                ' max: ' + this.options.maximum + ' value: ' +
                self.options.value);
            
            // Build the slider and bind the event handlers.

            self.build_slider();
            self.set_label(self.options.value);
            
            var bar = $(this.container_element).find(self.id_selector() +
                                                     ' .bar')[0];
            var offset = $(bar).offset();
            this.bar_left_offset = offset.left;
            console.log('bar_left_offset:', this.bar_left_offset);
            this.bar_width = $(bar).width();
            console.log('bar_width:', this.bar_width);

            var thumb = $(this.container_element).find(self.id_selector() +
                                                       ' .thumb')[0];
            this.thumb_width = $(thumb).width();
            console.log('thumb_width:', this.thumb_width);

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

                $(this.container_element).unbind('mousemove.Slider');
                $(this.container_element).unbind('mouseup.Slider');

                $(this.container_element).bind({
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
