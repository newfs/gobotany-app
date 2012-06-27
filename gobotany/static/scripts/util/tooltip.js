define([
    'bridge/jquery'
], function($) {
    // Constructor
    var Tooltip = function (elements, options) {
        this.elements = elements;
        this.options = $.extend({}, this.defaults, options);
        this.init();
    };
    // Prototype definition
    Tooltip.prototype = {
        defaults: {
            css_class: 'gb-tooltip'
        },

        build_tooltip: function (content) {
            var element = $('<div class="' + this.options.css_class + '">' +
                            content + '</div>');
            return element;
        },

        show_tooltip: function (element, left, top) {
            // If a tooltip is already showing, skip.
            if ($('.' + this.options.css_class).length > 0) {
                return;
            }

            var tooltip_element = this.build_tooltip(this.options.content);
            //console.log($('<div>').append(tooltip_element).clone().html());
            $('body').append(tooltip_element);

            var tooltip_height = $(tooltip_element).height();
            tooltip_element.css({
                'left': left,
                'top': top - tooltip_height - 20
            });
        },

        hide_tooltip: function () {
            $('.' + this.options.css_class).remove();
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
                $(element).bind({
                    // For point-and-click interfaces, activate on hover.
                    'mouseenter.Tooltip': function () {
                        var offset = $(element).offset();
                        self.show_tooltip(element, offset.left, offset.top);
                    },
                    'mouseleave.Tooltip': function () {
                        self.hide_tooltip();
                    },
                    // For touch interfaces, activate on tap.
                    'touchend.Tooltip': function (event) {
                        var offset = $(element).offset();
                        self.toggle_tooltip(element, offset.left, offset.top);

                        // Stop events from propagating onward to the
                        // document body. Otherwise the code that hides
                        // the tooltip would always run, and the tooltip
                        // would not show upon tap because it would be
                        // immediately hidden.
                        event.stopPropagation();
                        // Ensure the tooltip can be dismissed on the
                        // next touch following a touch with movement.
                        just_moved = false;
                    }
                });
            });   // end loop through elements

            // Hide the tooltip upon a tap anywhere.
            $('body').bind({
                'touchend.Tooltip_dismiss': function () {
                    // Only hide the tooltip if the user did not just
                    // move around when they last touched.
                    if (just_moved === false) {
                        self.hide_tooltip();
                    }
                    just_moved = false;
                },
                // Do not allow the tooltip to be hidden upon a touch event
                // that involves finger movement, because the user may be
                // trying to reposition the viewport in order to better
                // view the tooltip.
                'touchmove.Tooltip': function () {
                    just_moved = true;
                }
            });

        }   // end init()
    };   // end prototype definition

    // Extend jQuery with tooltip capability.
    $.fn.tooltip = function (options) {
        new Tooltip(this, options);
        return this;
    };
});
