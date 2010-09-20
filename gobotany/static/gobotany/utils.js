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
    if (nodes.length === undefined)
        nodes = [nodes];

    setTimeout(function() {
        for (var x = 0; x < nodes.length; x++)
            dojo.anim(nodes[x], {backgroundColor: 'white'});
    }, 2000);
};

gobotany.utils.clone = function(obj, updated_args) {
    var new_obj = (obj instanceof Array) ? [] : {};
    for (i in obj) {
        new_obj[i] = obj[i]
    }

    if (updated_args !== undefined) {
        for (var x in updated_args)
            if (updated_args.hasOwnProperty(x))
                new_obj[x] = updated_args[x];
    }

    return new_obj;
};

gobotany.utils.pretty_length = function(unit, value) {
    var ret = {
        metric: String(value.toFixed(2)) + unit
    };

    var valuemm = value;
    if (unit == 'cm')
        valuemm = 10 * valuemm;
    else if (unit == 'm')
        valuemm = 1000 * valuemm;

    var inches = 0.0393700787 * valuemm;
    var remaining = null;
    if (inches > 12) {
        var feet = inches / 12;
        feet = feet.toFixed(2);
        inches = inches % 12;
        inches = inches.toFixed(2);
        remaining = String(feet) + "'" + String(inches) + '"';
    } else {
        inches = inches.toFixed(2);
        remaining = String(inches) + '"'
    }
    
    ret.imperial = remaining;

    return ret;
};


dojo.declare("gobotany.utils.UnitFieldsUpdater", null, {
    constructor: function(input1, input2, unit) {
        this.input1 = input1;
        this.input2 = input2;
        this.unit = unit;
        this.realvalue = null;
        this.did_they_just_choose_a_genus = false;
    },

    update_fields: function(value) {
        this.realvalue = value;
        pretty = gobotany.utils.pretty_length(this.unit, value);

        var unit = this.unit;

        dojo.attr(this.input1, 'value', pretty.metric);
        dojo.attr(this.input2, 'value', pretty.imperial);
    }
});
