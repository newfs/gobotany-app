dojo.provide('gobotany.utils');


// notify()
// display a notification message at the top of the page
// that will eventually fade away
gobotany.utils.notify = function(txt) {
    var holder = dojo.byId('notification-msg');
    if (holder === null) {
        holder = dojo.place('<div class="hidden" id="notification-msg"></div>',
                            dojo.body());
    }

    holder.innerHTML = txt;

    var wbox = dojo.window.getBox();
    var holderbox = dojo.position(holder);

    var left = (wbox.w / 2) - (holderbox.w / 2);
    var top = wbox.t;
    dojo.style(holder,
               {position: 'absolute',
                top: top + 'px',
                left: left + 'px'});

    dojo.removeClass(holder, 'hidden');
    dojo.fadeIn({node: holder, duration: 1}).play();

    setTimeout(function() {
        dojo.fadeOut({node: holder}).play();
    }, 5000);
};

gobotany.utils.animate_changed = function(node) {
    var nodes = node;
    if (nodes.length === undefined) {
        nodes = [nodes];
    }

    var animation = nodes.animateProperty({
        duration: 2000,
        properties: {
            backgroundColor: {
                start: '#ff0',
                end: '#fff'
            }
        },
        onEnd: function() {
            // When the animation is done, remove the inline style
            // property containing the background color so it will
            // not interfere with future hover or selection states.
            nodes.removeAttr('style');
        }
    });
    animation.play();
};

gobotany.utils.clone = function(obj, updated_args) {
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
};

gobotany.utils.pretty_length = function(unit, mmvalue) {
    var SPACE = '&#160;';
    var mm = parseFloat(mmvalue); /* make sure it is a float */
    if (isNaN(mm)) {
        console.log('gobotany.utils.pretty_length: ' + mmvalue +
                    ' is not a number');
    }
    if (unit == 'mm') {
        return mm.toFixed(1) + SPACE + 'mm';
    } else if (unit == 'cm') {
        return (mm / 10.0).toFixed(1) + SPACE + 'cm';
    } else if (unit == 'm') {
        return (mm / 1000.0).toFixed(2) + SPACE + 'm';
    }
    inches = mm / 25.4;
    feet = Math.floor(inches / 12.0);
    inches = inches % 12.0;
    var value = '';
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
    if (wholein == 0 && eighths == 0) {
        value += '0';
    }
    value += SPACE + 'in';
    return value;
};

/* Programatically click a link, running its attached event handlers as if a
   user clicked it.

   Code based on the answer provided by Matthew Crumley at:
   http://stackoverflow.com/questions/902713/how-do-i-automatically-click-a-link-with-javascript
 */
gobotany.utils.click_link = function(link) {
    if (document.createEvent) {
        var event = document.createEvent('MouseEvents');
        event.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0,
            false, false, false, false, 0, null);
        link.dispatchEvent(event);
    } else if (link.fireEvent) {
        link.fireEvent('onclick');
    }
};

