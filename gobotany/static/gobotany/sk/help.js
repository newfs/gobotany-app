/* Code for adding behavior to the Help pages. */

// Configure this module here until we finish the migration
define(['dojo/_base/declare',
        'dojo/query',
        'dojo/dom-geometry',
        'dojo/_base/array',
        'dojo/dom-class',
        'dojo/dom-style',
        'dojo/_base/connect',
        'dojo/_base/lang'],
    function(declare, query, domGeom, array, domClass, domStyle, connect,
             lang) {
        return declare('gobotany.sk.help.MapToGroupsHelper', null, {
            groups: null,
            subgroup_sets: null,

            constructor: function () {
                this.groups = query('.plant-group');
                this.subgroup_sets = query('.subgroups');
            },

            get_left_margin_for_subgroup_set: function (group_number) {
                /* Get the left margin for a subgroup set that will attempt
                   to center the subgroup set below its group to the extent
                   possible. */

                // Get the first group's horizontal left position, which is
                // at the left edge of the content area.
                var first_group_left_x_position =
                    domGeom.position(this.groups[0]).x;

                // Get the last group's horizontal right position, which is
                // at the right edge of the content area.
                var last_group_position =
                    domGeom.position(this.groups[this.groups.length - 1]);
                var last_group_right_x_position = last_group_position.x +
                    last_group_position.w;

                // Get the group's horizontal center position.
                var group_position =
                    domGeom.position(this.groups[group_number]);
                var group_center_x_position = group_position.x +
                    Math.floor(group_position.w / 2);

                /* Get the width of the subgroup set by tallying the widths
                   of the subgroups within it. This is necessary because the
                   subgroups have CSS float applied, so their parent
                   container's width does not reflect the total width of the
                   subgroups. */
                var subgroup_set_width = 0;
                var subgroup_set = this.subgroup_sets[group_number];
                array.forEach(query('.plant-subgroup', subgroup_set),
                    function(subgroup, i) {
                        var subgroup_width = domGeom.position(subgroup).w;
                        subgroup_set_width += subgroup_width;
                    }
                );

                // Get the maximum left margin allowed for the subgroup set.
                var EXTRA_PADDING = 22;  // Will subtract to ensure fit
                var maximum_left_margin = last_group_right_x_position -
                    first_group_left_x_position - subgroup_set_width -
                    EXTRA_PADDING;

                // Calculate the left margin based on positions and widths.
                var left_margin = group_center_x_position -
                    Math.floor(subgroup_set_width / 2) - 
                    first_group_left_x_position;

                // If this is the last group, tweak the left margin for
                // better right alignment.
                if (group_number === this.groups.length - 1) {
                    maximum_left_margin += 11;
                }

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

                this.groups.forEach(function(group, i) {
                    if (i === group_number) {
                        domClass.add(group, ACTIVE_CLASS);
                    }
                    else {
                        domClass.remove(group, ACTIVE_CLASS);
                    }
                });

                var that = this;
                this.subgroup_sets.forEach(function(subgroup_set, i) {
                    if (i === group_number) {
                        // Show the subgroup set.
                        domClass.remove(subgroup_set, HIDDEN_CLASS);
                        var left_margin_value =
                            that.get_left_margin_for_subgroup_set(i);
                        domStyle.set(subgroup_set, 'marginLeft',
                            left_margin_value.toString() + 'px');
                    }
                    else {
                        // Hide the subgroup set.
                        domClass.add(subgroup_set, HIDDEN_CLASS);
                    }
                });
            },

            setup: function () {
                // Attach click events to groups to show their subgroups.
                var i;
                for (i = 0; i < this.groups.length; i += 1) {
                    var group = this.groups[i];
                    connect.connect(group, 'onclick',
                        lang.hitch(this, this.activate_group, i));
                }

                // Initially activate the first group and its subgroup set.
                this.activate_group(0);
            }

        });
    }
);
