/* Length slider that looks something like a ruler. */

dojo.provide('gobotany.sk.RulerSlider');
dojo.require('dijit.form.HorizontalSlider');
dojo.require('dijit.form.HorizontalRule');
dojo.require('dijit.form.HorizontalRuleLabels');

dojo.declare('gobotany.sk.RulerSlider', null, {

    constructor: function(node, themin, themax, startvalue, updater) {

        var slider = new dijit.form.HorizontalSlider({
            name: 'character_slider',
            showButtons: false,
            value: startvalue,
            minimum: themin,
            maximum: themax,
            intermediateChanges: true,
            style: 'width: 600px;',
            onChange: dojo.hitch(updater, updater.update_fields)
        }, node);

        var distance = themax - themin;
        var ticks_count = this.get_ticks_labels_count(themin, themax);

        /* Figure out how many tick marks to use. */

        var base = 0.1; /* minimum permissible distance between labels (mm) */
        var done = false;
        while (!done) {
            var intervals = [base, base * 5];
            for (var key in intervals) {
                var interval = intervals[key];
                var labelcount = Math.floor(distance / interval);
                if (labelcount < 19) {
                    done = true;
                    break;
                }
            }
            if (!done)
                base = base * 10;
        }

        if (distance > 3100.0) {
            var factor = 1000.0;
            var unit = 'm';
        } else if (distance > 31.0) {
            var factor = 10.0;
            var unit = 'cm';
        } else {
            var factor = 1.0;
            var unit = 'mm';
        }
        fixdigits = (base / factor < 1) ? 1 : 0; /* show '25.0' or just '25' */

        var mylabels = [''];
        for (var i = 1; i <= labelcount; i++) {
            mylabels.push('' + (interval * i / factor).toFixed(fixdigits));
        }
        mylabels[mylabels.length - 1] += '<br>' + unit;

        var labelswidth = 600 * (labelcount * interval) / distance;

        console.log(base, interval);

        /* And draw the labels. */

        var tickcount = distance / Math.max(0.1, base) + 1;
        var labelcount = distance / interval + 1;

        var node = dojo.create('div', null, slider.containerNode);
        var ruleticks = new dijit.form.HorizontalRule({
            container: 'topDecoration',
            count: tickcount,
            style: 'height: 7px;'
        }, node);

        var node = dojo.create('div', null, slider.containerNode);
        var ruleticks = new dijit.form.HorizontalRule({
            container: 'topDecoration',
            count: labelcount,
            style: 'height: 5px;'
        }, node);

        var labels_node = dojo.create('div', null, slider.containerNode);
        /*var mylabels = this.get_labels(themin, themax, ticks_count);*/
        var rule_labels = new dijit.form.HorizontalRuleLabels({
            container: 'topDecoration',
            labels: mylabels,
            style: 'height:2.5em; font-size:75%; color:#000; width: ' +
                labelswidth + 'px;'
        }, labels_node);

        var rule_node2 = dojo.create('div', null, slider.containerNode);
        var ruleticks2 = new dijit.form.HorizontalRule({
            container: 'topDecoration',
            count: ticks_count,
            style: 'height: 10px;'
        }, rule_node2);
    },

    get_ticks_labels_count: function(min, max) {
        // Get the number of ticks and labels for the slider.
        // If the number is too high for the allotted screen space,
        // cut it down to a reasonable number.
        var MAX_NUMBER = 10;
        var number = max - min + 1;
        while (number > MAX_NUMBER) {
            number = Math.round(number / 2);
        }
        return number;
    },

    get_labels: function(min, max, number_of_ticks) {
        // Return a list of labels for the given range and number of ticks.
        var labels = [];
        var number_of_segments = number_of_ticks - 1;

        labels.push('');
        for (i = 1; i < number_of_segments; i++) {
            var label_value = ((max - min) / number_of_segments) * i;
            labels.push(String(label_value.toFixed(1)));
        }
        labels.push(String(max.toFixed(1)) + '<br>mm');

        return labels;
    }

});
