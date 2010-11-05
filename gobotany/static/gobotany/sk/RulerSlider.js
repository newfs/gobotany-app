/* Length slider that looks something like a ruler. */

dojo.provide('gobotany.sk.RulerSlider');
dojo.require('dijit.form.HorizontalSlider');
dojo.require('dijit.form.HorizontalRule');
dojo.require('dijit.form.HorizontalRuleLabels');

dojo.declare('gobotany.sk.RulerSlider', null, {

    constructor: function(node, pxwidth, themin, themax, startvalue, updater) {
        this.pxwidth = pxwidth;

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

        var mylabels1 = [''];  /* for the measurements */
        var mylabels2 = [''];  /* for the units, in the last label */
        for (var i = 1; i <= labelcount; i++) {
            mylabels1.push('' + (interval * i / factor).toFixed(fixdigits));
            mylabels2.push(i == labelcount ? unit : '');
        }

        var labelswidth = pxwidth * (labelcount * interval) / distance;

        console.log(base, interval);

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

        /* The bottom of the ruler goes in the opposite order: English
        labels, then their big tick marks, then little tick marks. */

        var labels_node = dojo.create('div', null, slider.containerNode);
        var rule_labels = new dijit.form.HorizontalRuleLabels({
            container: 'topDecoration',
            labels: mylabels2,
            style: 'height:1.5em; font-size:75%; color:#000; width: ' +
                labelswidth + 'px;'
        }, this.new_div());

        var labels_node = dojo.create('div', null, slider.containerNode);
        var rule_labels = new dijit.form.HorizontalRuleLabels({
            container: 'topDecoration',
            labels: mylabels1,
            style: 'height:1em; font-size:75%; color:#000; width: ' +
                labelswidth + 'px;'
        }, this.new_div());

        var node = dojo.create('div', null, slider.containerNode);
        var ruleticks = new dijit.form.HorizontalRule({
            container: 'topDecoration',
            count: labelcount,
            style: 'height: 5px;'
        }, this.new_div());

        var node = dojo.create('div', null, slider.containerNode);
        var ruleticks = new dijit.form.HorizontalRule({
            container: 'topDecoration',
            count: tickcount,
            style: 'height: 7px;'
        }, this.new_div());
    },

    new_div: function() {
        return dojo.create('div', null, this.slider.containerNode);
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
