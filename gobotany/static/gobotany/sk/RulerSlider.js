/* Length slider that looks something like a ruler. */

dojo.provide('gobotany.sk.RulerSlider');
dojo.require('dijit.form.HorizontalSlider');
dojo.require('dijit.form.HorizontalRule');
dojo.require('dijit.form.HorizontalRuleLabels');

dojo.declare('gobotany.sk.RulerSlider', null, {

    min_pixels_per_tick: 4.0,
    min_pixels_per_label: 25.0,

    constructor: function(node, pxwidth, themin, themax, startvalue, updater) {
        this.pxwidth = pxwidth;
        var distance = this.mmwidth = themax - themin;

        var slider = this.slider = new dijit.form.HorizontalSlider({
            name: 'character_slider',
            showButtons: false,
            value: startvalue,
            minimum: themin,
            maximum: themax,
            intermediateChanges: true,
            style: 'width: ' + pxwidth + 'px;',
            onChange: dojo.hitch(updater, updater.update_fields)
        }, node);

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

        var mylabels1 = [''];  /* for the measurements */
        var mylabels2 = [''];  /* for the units, in the last label */
        for (var i = 1; i <= labelcount; i++) {
            mylabels1.push('' + (interval * i / factor).toFixed(fixdigits));
            mylabels2.push(i == labelcount ? unit : '');
        }

        var labelswidth = pxwidth * (labelcount * interval) / distance;

        /* The top of the ruler contains little tick marks, then big
        tick marks, then finally the metric labels. */

        var tickcount = distance / Math.max(0.1, base) + 1;
        var labelcount = distance / interval + 1;

        var ruleticks = new dijit.form.HorizontalRule({
            container: 'topDecoration',
            count: tickcount,
            style: 'height: 7px;'
        }, this.new_div());

        var ruleticks = new dijit.form.HorizontalRule({
            container: 'topDecoration',
            count: labelcount,
            style: 'height: 5px;'
        }, this.new_div());

        var rule_labels = new dijit.form.HorizontalRuleLabels({
            container: 'topDecoration',
            labels: mylabels1,
            style: 'height:0.8em; font-size:75%; color:#000; width: ' +
                labelswidth + 'px;'
        }, this.new_div());

        var rule_labels = new dijit.form.HorizontalRuleLabels({
            container: 'topDecoration',
            labels: mylabels2,
            style: 'height:1.5em; font-size:75%; color:#000; width: ' +
                labelswidth + 'px;'
        }, this.new_div());

        /* The bottom of the ruler goes in the opposite order: English
        labels, then their big tick marks, then little tick marks. */

        var labels_and_ticks = this.compute_ruler([
            [0.396875, null], // sixty-fourths
            [1.5875, null], // sixteenths
            [6.35, null],   // quarters
            [25.4, 'in'],   // inches
            [152.4, null],  // half-feet
            [304.8, 'ft']   // feet
        ]);
        labels_and_ticks.reverse();
        this.draw_labels_and_ticks(labels_and_ticks);
    },

    draw_labels_and_ticks: function(labels_and_ticks) {

        for (i in labels_and_ticks) {
            thing = labels_and_ticks[i];

            if (typeof thing === 'number') {  /* number means do tick marks */
                var tickheight = (i == 0 || i == labels_and_ticks.length - 1) ?
                    6 : 4;  /* lowest set of ticks should be longer */
                new dijit.form.HorizontalRule({
                    container: 'topDecoration',
                    count: thing + 1,
                    style: 'height: ' + tickheight + 'px;'
                }, this.new_div());

            } else { /* otherwise this will be [pxwidth, [label, ...]] */
                var labels_width = thing[0];
                var labels_array = thing[1];
                var rule_labels = new dijit.form.HorizontalRuleLabels({
                    container: 'topDecoration',
                    labels: labels_array,
                    style: 'height:1em; font-size:75%; color:#000; width: ' +
                        labels_width + 'px;'
                }, this.new_div());
            }
        }

    },

    new_div: function() {
        return dojo.create('div', null, this.slider.containerNode);
    },

    compute_ruler: function(unitlist) {
        var results = [];  /* list of label sequences and tick counts */
        var max_ticks = this.pxwidth / this.min_pixels_per_tick;
        var max_labels = this.pxwidth / this.min_pixels_per_label;

        for (var i in unitlist) {
            var length = unitlist[i][0];
            var label = unitlist[i][1];
            var count = this.mmwidth / length;
            if (count > max_ticks)
                continue;
            if (count < 1.0) /* include no tick rows on which no tick fits */
                break;
            results.push(count);
        }

        for (var i in unitlist) {
            var length = unitlist[i][0];
            var label = unitlist[i][1];
            if (label === null)
                continue;  /* cannot label these */
            var count = Math.floor(this.mmwidth / length);
            if (count > max_labels)
                continue;  /* cannot label this small a unit */

            var nlabels = [''];  /* leftmost/zero label is always blank */
            var ulabels = [];
            for (var j = 1; j <= count; j++) {
                nlabels.push('' + j);
                ulabels.push('');
            }
            ulabels.push(label);

            results.push([
                this.pxwidth * count * length / this.mmwidth, nlabels
            ]);
            results.push([
                this.pxwidth * count * length / this.mmwidth, ulabels
            ]);
            break;
        }

        return results;
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
    }
});
