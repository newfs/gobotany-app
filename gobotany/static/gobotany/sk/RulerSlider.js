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

        this.slider = new dijit.form.HorizontalSlider({
            name: 'character_slider',
            showButtons: false,
            value: startvalue,
            minimum: themin,
            maximum: themax,
            intermediateChanges: true,
            style: 'width: ' + pxwidth + 'px;',
            onChange: dojo.hitch(updater, updater.update_fields)
        }, node);

        /* Put metric on top. */

        var labels_and_ticks = this.compute_ruler([
            [0.1, null, 0.1],
            [0.5, 'mm', 0.5],
            [1.0, 'mm', 1.0],
            [5.0, 'mm', 5.0],
            [10.0, 'cm', 1.0],
            [50.0, 'cm', 5.0],
            [100.0, 'cm', 10.0],
            [500.0, 'm', 0.5],
            [1000.0, 'm', 1.0]
        ], false);
        this.draw_labels_and_ticks(labels_and_ticks);

        /* And the English measures go on bottom. */

        var labels_and_ticks = this.compute_ruler([
            [0.396875, null, 0.0625], // sixty-fourths
            [3.175, 'in', 0.125], // eighths
            [6.35, 'in', 0.25],   // quarters
            [25.4, 'in', 1.0],   // inches
            [152.4, 'ft', 0.5],  // half-feet
            [304.8, 'ft', 1.0]   // feet
        ], true);
        labels_and_ticks.reverse();
        this.draw_labels_and_ticks(labels_and_ticks);

        /* Add a second handle below the English tick marks. */

        var handles = dojo.query('.dijitSliderImageHandleH');
        var handle = handles[handles.length - 1];
        var secondhandle = dojo.create('div', {
            class: 'secondhandle',
            style: 'top: ' + dojo.position(this.slider.containerNode).h + 'px'
        }, handle);

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

    compute_ruler: function(unitlist, vulgar) {
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
            var per = unitlist[i][2];
            if (label === null)
                continue;  /* cannot label these */
            var count = Math.floor(this.mmwidth / length);
            if (count > max_labels)
                continue;  /* cannot label this small a unit */

            var nlabels = [''];  /* leftmost/zero label is always blank */
            var ulabels = [];
            for (var j = 1; j <= count; j++) {
                if (vulgar) {
                    /* English lengths use vulgar fractions */
                    var whole = '' + Math.floor(j * per);
                    var eighths = Math.round(8 * j * per) % 8;
                    nlabels.push(eighths ? ' ⅛¼⅜½⅝¾⅞'[eighths] : whole);
                } else {
                    /* Metric lengths get to use a simple decimal point */
                    nlabels.push('' + (j * per).toFixed(per < 1 ? 1 : 0));
                }
                ulabels.push('');
            }
            ulabels.push(label);

            var totalwidth = this.pxwidth * count * length / this.mmwidth;
            results.push([totalwidth, nlabels]);
            results.push([totalwidth, ulabels]);
            break;
        }

        return results;
    }
});
