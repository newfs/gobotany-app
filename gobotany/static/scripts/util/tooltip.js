define([
    'bridge/jquery'
], function($) {
    // Constructor
    var Tooltip = function (elements, options) {
        this.elements = elements;
        this.options = options;
        this.init();
    };
    // Prototype definition
    Tooltip.prototype = {

        log_content: function (element) {
            console.log('log_content:', this.options.content);
        },

        show_tooltip: function (element) {
            console.log('TODO: show tooltip for this element');
        },

        hide_tooltip: function (element) {
            console.log('TODO: hide tooltip for this element:',
                        this.options.content);
        },

        toggle_tooltip: function (element) {
            // This function is called when a tooltip element is
            // clicked (or tapped) and so the tooltip should either
            // be shown (if it currently is hidden) or hidden (if
            // it currently is shown).
            console.log('TODO: toggle tooltip for this element');
        },

        init: function () {
            var self = this;
            
            this.elements.each(function (index, element) {
                $(element).bind({
                    // For point-and-click interface, support hover
                    'mouseenter.Tooltip': function () {
                        console.log('mouseenter');
                        //self.log_content(element);
                        self.show_tooltip(element);
                    },
                    'mouseleave.Tooltip': function () {
                        console.log('mouseleave');
                        //self.log_content(element);
                        self.hide_tooltip(element);
                    },
                    // For touch interface, support tap
                    'click.Tooltip': function () {
                        console.log('click');
                        //self.log_content(element);
                        self.toggle_tooltip(element);
                    }
                });

                // Bind an event to each of the element's parent
                // elements that hides the tooltip if clicked or
                // tapped.
                // TODO: will want to bind this instead to the parents
                // of the dynamically-created tooltip div itself, not
                // the element div to which the tooltip is attached.
                $(element).parents('div').each(function (parent_index,
                                                         parent_element) {
                    $(parent_element).bind({
                        'click.Tooltip_dismiss': function () {
                            console.log('click: tooltip dismiss');
                            self.hide_tooltip(element);
                        }
                    });
                });  // end loop through parents

            });   // end loop through elements
        }

    };

    // Extend jQuery with tooltip capability.
    $.fn.tooltip = function (options) {
        new Tooltip(this, options);
        return this;
    };
    
});
