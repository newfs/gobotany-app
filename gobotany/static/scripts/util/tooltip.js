define([
    'bridge/jquery'
], function($) {
    // Constructor
    var Tooltip = function (elements, options) {
        this.elements = elements;
        this.options = $.extend({}, this.defaults, options);
        this.is_touch = navigator.userAgent.match(
                        /(iPad|iPod|iPhone|Android)/) ? true : false;
        this.init();
    };
    // Prototype definition
    Tooltip.prototype = {
        defaults: {
            arrow_css_class: 'arrow',
            arrow_edge_margin: 10,
            css_class: 'gb-tooltip',
            fade_speed: 'fast',
            horizontal_adjust_px: 20,
            hover_delay: 400,
            small_screen_max_width: 600,
            vertical_adjust_px: 24,
            width: null   // use width defined in CSS by default
        },

        build_tooltip: function (content) {
            var element = $('<div class="' + this.options.css_class + '">' +
                            content + '<div class="arrow"></div></div>');
            return element;
        },

        position_tooltip: function (tooltip_element, left, top) {
            var activating_element_position = left;

            // If the element that activated the tooltip is far enough
            // to the right side of the viewport that the tooltip would
            // not fit in the visible area, make the tooltip appear far
            // enough to the left to make it fit.
            var tooltip_width = $(tooltip_element).width();
            var viewport_width = $(window).width();
            var scroll_left = $(window).scrollLeft();
            var visual_left_edge = left - scroll_left;
            var visual_right_edge = visual_left_edge + tooltip_width;
            if (visual_right_edge >= viewport_width) {
                left = viewport_width - tooltip_width - 
                       this.options.horizontal_adjust_px + scroll_left;
            }
            // If the horizontal position would start off the screen to
            // the left, adjust it to start at the left edge.
            if (left < scroll_left) {
                left = scroll_left;
            }
    
            // Set the tooltip position.
            var tooltip_height = $(tooltip_element).height();
            tooltip_element.css({
                'left': left,
                'top': top - tooltip_height - this.options.vertical_adjust_px
            });

            // Set the arrow position.
            var arrow_selector = '.' + this.options.css_class + ' .' +
                                 this.options.arrow_css_class;
            var arrow_element = $(arrow_selector);
            var tooltip_left_adjustment = activating_element_position - left;
            var arrow_position = tooltip_left_adjustment;
            if (arrow_position <= 0) {
                arrow_position = this.options.arrow_edge_margin;
            }
            if (arrow_position > tooltip_width) {
                arrow_position = tooltip_width -
                                 this.options.arrow_edge_margin;
            }
            arrow_element.css({'left': arrow_position});
        },

        show_tooltip: function (element, left, top) {
            // If a tooltip is already showing, skip.
            if ($('.' + this.options.css_class).length > 0) {
                return;
            }

            var tooltip_element = this.build_tooltip(this.options.content);

            // If a CSS width value was supplied for the tooltip, use it
            // to override the external CSS.
            if (this.options.width !== null) {
                tooltip_element.css({'width': this.options.width });
            }

            $('body').append(tooltip_element);
            this.position_tooltip(tooltip_element, left, top);
            $(tooltip_element).fadeIn(this.options.fade_speed);
        },

        hide_tooltip: function () {
            var tooltip = '.' + this.options.css_class;
            $(tooltip).fadeOut(this.options.fade_speed, function () {
                $(tooltip).remove();
            });
        },

        toggle_tooltip: function (element, left, top) {
            if ($('.' + this.options.css_class).length > 0) {
                this.hide_tooltip();
            }
            else {
                this.show_tooltip(element, left, top);
            }
        },

        init: function () {
            var self = this;
            var just_moved = false;

            this.elements.each(function (index, element) {
                if (self.is_touch) {
                    // For touch interfaces, activate on tap.
                    $(element).bind({
                        'touchend.Tooltip': function (event) {
                            var offset = $(element).offset();
                            self.toggle_tooltip(element, offset.left,
                                                offset.top);

                            // Stop events from propagating onward to the
                            // document body. Otherwise the code that
                            // dismisses the tooltip would always run, and
                            // the tooltip would not show upon tap because
                            // it would immediately be hidden.
                            event.stopPropagation();
                            // Ensure the tooltip can be dismissed on the
                            // next touch following a touch with movement.
                            just_moved = false;
                        }
                    });
                }
                else {
                    // For point-and-click interfaces, activate on hover.
                    $(element).bind({
                        'mouseenter.Tooltip': function () {
                            var offset = $(element).offset();
                            // Delay the hover a bit to avoid accidental
                            // activation when moving the cursor quickly by.
                            this.timeout_id = window.setTimeout(
                                function (element) {
                                    self.show_tooltip(element, offset.left, 
                                                      offset.top);
                                },
                                self.options.hover_delay, element);
                        },
                        'mouseleave.Tooltip': function () {
                            // Clear any timeout set for delaying the hover.
                            if (typeof this.timeout_id === 'number') {  
                                window.clearTimeout(this.timeout_id);  
                                delete this.timeout_id;  
                            }
                            
                            self.hide_tooltip();
                        }
                    });
                }
            });   // end loop through elements

            // For touch interfaces, dismiss the tooltip upon a tap anywhere.
            if (self.is_touch) {
                $('body').bind({
                    'touchend.Tooltip_dismiss': function () {
                        // Only dismiss the tooltip if the user did not just
                        // move around when they last touched.
                        if (just_moved === false) {
                            self.hide_tooltip();
                        }
                        just_moved = false;
                    },
                    // Do not dismiss the tooltip upon a touch event that
                    // involves finger movement, because the user may be
                    // trying to reposition the viewport in order to better
                    // view the tooltip.
                    'touchmove.Tooltip': function () {
                        just_moved = true;
                    }
                });
            }

        }   // end init()
    };   // end prototype definition

    // Extend jQuery with tooltip capability.
    $.fn.tooltip = function (options) {
        new Tooltip(this, options);
        return this;
    };
});
