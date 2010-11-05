dojo.provide('gobotany.utils');


// notify()
// display a notification message at the top of the script
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

    setTimeout(function() {
        for (var x = 0; x < nodes.length; x++) {
            dojo.anim(nodes[x], {backgroundColor: 'white'});
        }
    }, 2000);
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
    var mm = parseFloat(mmvalue); /* make sure it is a float */
    if (isNaN(mm)) {
        console.log('gobotany.utils.pretty_length: ' + mmvalue +
                    ' is not a number');
    }
    if (unit == 'mm') {
        return mm.toFixed(1) + '&#8239;mm'; /* narrow space + unit */
    } else if (unit == 'cm') {
        return (mm / 10.0).toFixed(1) + '&#8239;cm';
    } else if (unit == 'm') {
        return (mm / 1000.0).toFixed(2) + '&#8239;m';
    }
    inches = mm / 25.4;
    feet = Math.floor(inches / 12.0);
    inches = inches % 12.0;
    var value = '';
    if (feet > 0) {
        value += feet + '&#8239;ft&nbsp;';
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
    value += '&#8239;in';
    return value;
};
