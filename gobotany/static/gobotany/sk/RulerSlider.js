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

        var ticks_count = this.get_ticks_labels_count(themin, themax);

        var rule_node = dojo.create('div', null, slider.containerNode);
        var ruleticks = new dijit.form.HorizontalRule({
            container: 'topDecoration',
            count: ticks_count,
            style: 'height: 10px;'
        }, rule_node);

        var labels_node = dojo.create('div', null, slider.containerNode);
        var mylabels = this.get_labels(themin, themax, ticks_count);
        var rule_labels = new dijit.form.HorizontalRuleLabels({
            container: 'topDecoration',
            count: ticks_count,
            labels: mylabels,
            style: 'height:1.5em; font-size:75%; color:#000; width: 600px;'
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
