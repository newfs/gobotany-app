define([
    'bridge/jquery'
], function($) {

    var utils = {
        // notify()
        // display a notification message at the top of the page
        // that will eventually fade away
        notify: function(txt) {
            var holder = $('#notification-msg');
            if (holder.length === 0) {
                holder = $('<div class="hidden" id="notification-msg"></div>')
                    .appendTo('body');
            }

            holder.html(txt);

            var win = $(window);

            var left = (win.width() / 2) - (holder.width() / 2);
            var top = win.scrollTop();
            holder.css({position: 'absolute',
                        top: top + 'px',
                        left: left + 'px'});

            holder.removeClass('hidden');
            holder.fadeIn(1000);

            setTimeout(function() {
                holder.fadeOut();
            }, 5000);
        },

        clone: function(obj, updated_args) {
            var new_obj = (obj instanceof Array) ? [] : {};
            for (i in obj) {
                new_obj[i] = obj[i];
            }

            if (updated_args !== undefined) {
                for (var x in updated_args)
                    if (updated_args.hasOwnProperty(x))
                        new_obj[x] = updated_args[x];
            }

            return new_obj;
        },

        pretty_length: function(unit, mmvalue, show_unit) {
            if (show_unit === undefined) {
                show_unit = true;
            }
            
            var SPACE = '\u00A0';
            var mm = parseFloat(mmvalue); /* make sure it is a float */
            if (isNaN(mm)) {
                console.log('gobotany.utils.pretty_length: ' + mmvalue +
                            ' is not a number');
            }
            var value = '';
            if (unit == 'mm') {
                value = mm.toFixed(2);
            } else if (unit === 'cm') {
                value = (mm / 10.0).toFixed(2);
            } else if (unit === 'm') {
                value = (mm / 1000.0).toFixed(2);
            } else {   // assume unit is 'in'
                unit = 'in';
                inches = mm / 25.4;
                feet = Math.floor(inches / 12.0);
                inches = inches % 12.0;
                if (feet > 0) {
                    value += feet + SPACE + 'ft' + SPACE;
                }
                var wholein = Math.floor(inches);
                if (wholein > 0) {
                    value += wholein;
                }
                var fracin = inches % 1.0;
                var eighths = Math.floor(fracin * 8.0);
                if (eighths > 0) {
                    value += ' ⅛¼⅜½⅝¾⅞'[eighths];
                }
                if (wholein === 0 && eighths === 0) {
                    value += '0';
                }
            }

            // If .0 or .00 is at the end, omit.
            if (value.indexOf('.00', value.length - 3) !== -1) {
                value = value.substring(0, value.length - 3);
            } else if (value.indexOf('.0', value.length - 2) !== -1) {
                value = value.substring(0, value.length - 2);
            } else if (/\d?\.\d+0/.test(value)) {
                // If 0 is at the end of a decimal, omit. (Ex.: 0.70 --> 0.7)
                value = value.substring(0, value.length - 1);
            }

            if (show_unit) {
                value += SPACE + unit;
            }

            return value;
        },

        /* Unit conversion for number values. Limited to current needs. */
        convert: function(source_value, source_unit, dest_unit) {
            var source_value = parseFloat(source_value), /* ensure it is a float */
                dest_value;

            if (isNaN(source_value)) {
                console.log('gobotany.utils.convert: ' + source_value +
                            ' is not a number');
            }
            if (source_unit === dest_unit) {
                dest_value = source_value;
            } else if (source_unit === 'cm' && dest_unit === 'mm') {
                dest_value = source_value * 10;
            } else if (source_unit === 'mm' && dest_unit === 'cm') {
                dest_value = source_value / 10;
            } else {
                console.log('gobotany.utils.convert: unknown conversion, returning ' +
                            'original value');
                dest_value = source_value;
            }

            return dest_value;
        },

        /* Programatically click a link, running its attached event handlers as if a
           user clicked it.

           Code based on the answer provided by Matthew Crumley at:
           http://stackoverflow.com/questions/902713/how-do-i-automatically-click-a-link-with-javascript
         */
        click_link: function(link) {
            if (document.createEvent) {
                var event = document.createEvent('MouseEvents');
                event.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0,
                    false, false, false, false, 0, null);
                link.dispatchEvent(event);
            } else if (link.fireEvent) {
                link.fireEvent('onclick');
            }
        }
    };

    // Allow us to create other modules that might inherit from this one
    // Currently, this object needs no initialization
    var instance = Object.create(utils);
    return instance;
});
