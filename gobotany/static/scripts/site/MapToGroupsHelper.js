/* Code for adding behavior to the Advanced Map to Groups page. */

define([
    'bridge/jquery'
], function($) {

        var MapsToGroupsHelper = {
            MAX_SMALL_SCREEN_WIDTH: 600,
            groups: null,
            subgroup_sets: null,

            init: function () {
                this.groups = $('.plant-group');
                this.subgroup_sets = $('.subgroups');
            },

            get_left_margin_for_subgroup_set: function (group_number) {
                /* Get the left margin for a subgroup set that will attempt
                   to center the subgroup set below its group to the extent
                   possible. */

                // Get the first group's horizontal left position, which is
                // at the left edge of the content area.
                var first_group_left_x_position = this.groups.offset().left;

                // Get the last group's horizontal right position, which is
                // at the right edge of the content area.
                var last_group = this.groups.last();
                var last_group_right_x_position = last_group.offset().left +
                    last_group.width();

                // Get the group's horizontal center position.
                var group = $(this.groups[group_number]);
                var group_center_x_position = group.offset().left +
                    Math.floor(group.width() / 2);

                /* Get the width of the subgroup set by tallying the widths
                   of the subgroups within it. This is necessary because the
                   subgroups have CSS float applied, so their parent
                   container's width does not reflect the total width of the
                   subgroups. */
                var subgroup_set_width = 0;
                var subgroup_set = $(this.subgroup_sets[group_number]);
                subgroup_set
                    .find('.plant-subgroup')
                    .each(function(i, subgroup) {
                        subgroup_set_width += $(subgroup).width();
                });

                // Get the maximum left margin allowed for the subgroup set.
                var EXTRA_PADDING = 22;  // Will subtract to ensure fit
                var maximum_left_margin = last_group_right_x_position -
                    first_group_left_x_position - subgroup_set_width -
                    EXTRA_PADDING;

                // Calculate the left margin based on positions and widths.
                var left_margin = group_center_x_position -
                    Math.floor(subgroup_set_width / 2) - 
                    first_group_left_x_position;

                // If the left margin is out of bounds, correct it.
                if (left_margin < 0) {
                    left_margin = 0;
                }
                else if (left_margin >= maximum_left_margin) {
                    left_margin = maximum_left_margin;
                }

                return left_margin;
            },

            activate_group: function (group_number) {
                /* Show a group and its set of subgroups. Rely on the order
                   of the groups and the subgroups as they appear in the
                   document: for example, the second group in the document
                   goes with the second subgroup set in the document. */

                var ACTIVE_CLASS = 'active';
                var HIDDEN_CLASS = 'hidden';

                this.groups.each(function(i, group) {
                    if (i === group_number) {
                        $(group).addClass(ACTIVE_CLASS);
                    }
                    else {
                        $(group).removeClass(ACTIVE_CLASS);
                    }
                });

                this.subgroup_sets.each($.proxy(function(i, subgroup_set) {
                    if (i === group_number) {
                        // Show the subgroup set.
                        $(subgroup_set).removeClass(HIDDEN_CLASS);

                        // If not viewing on a small screen, adjust the
                        // left margins so the subgroups align beneath
                        // the groups.
                        if ($(window).width() > this.MAX_SMALL_SCREEN_WIDTH) {
                            var left_margin_value =
                                this.get_left_margin_for_subgroup_set(i);
                            $(subgroup_set).css('marginLeft',
                                left_margin_value.toString() + 'px');
                        }
                    }
                    else {
                        // Hide the subgroup set.
                        $(subgroup_set).addClass(HIDDEN_CLASS);
                    }
                }, this));
            },

            setup: function () {
                // Attach click events to groups to show their subgroups.
                var i;
                for (i = 0; i < this.groups.length; i += 1) {
                    var group = this.groups[i];
                    $(group).bind('click', {groupNumber: i},
                        $.proxy(function(event) {
                            this.activate_group(event.data.groupNumber);

                            // On small screens: upon selecting a group,
                            // scroll the subgroups into view.
                            if ($(window).width() <=
                                this.MAX_SMALL_SCREEN_WIDTH) {

                                var subgroups = $('#subgroup-section').get(0);
                                subgroups.scrollIntoView();
                            }
                        }, this));
                }

                // Initially activate the first group and its subgroup set.
                this.activate_group(0);
            }

        };

        // Create a small factory method to return, which will act
        // as a little instance factory and constructor, so the user
        // can do as follows:
        // var obj = MyClassName(something, somethingelse);
        function factory() {
            var instance = Object.create(MapsToGroupsHelper);
            instance.init();
            return instance;
        }

        return factory;
    }
);
