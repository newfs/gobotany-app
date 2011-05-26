/*
 * Classes that create and maintain the working area.
 *
 * Upon instantiation, a working-area class draws the entire working area
 * for the filter that it has been given, and then un-hides the working
 * area.  Once up and running, it responds to three calls from outside
 * telling it that the outside world has changed.  It is also responsible
 * for handling every click and interaction inside the working area, and
 * for - when appropriate - forwarding the change in the filter state to
 * the outside world.
 *
 * Inputs:
 *
 * clear() - the user has pressed the "x" next to the filter's name in
 *     the sidebar summary, and the filter value should be cleared. [TODO]
 * set_species_vector(vector) - some other filter has changed or cleared,
 *     so the set of available species has changed; the counts next to
 *     each character value should be changed, or, for a length filter,
 *     the set of allowable input ranges.
 * dismiss() - the filter working area should be dismissed.
 *
 * Outputs:
 *
 * on_change(filter) - the working area invokes this callback whenever
 *     a user action has caused the filter value to be selected and set.
 */

/* TODO
 *
 * - Get clear() working, and have the manager call it.
 * - Get dismiss() working, and have the manager call it.
 */

dojo.provide('gobotany.sk.working_area');

dojo.require('dojo.NodeList-html');

/**
 * Return the correct working area class for a given filter.
 *
 * @param {Filter} filter The filter for which you want a working area.
 * @return {Class} The class that will manage this kind of working area.
 */
gobotany.sk.working_area.select_working_area = function(filter) {
    if (filter.value_type == 'TEXT') {
        return gobotany.sk.working_area.Choice;
    } else
        console.log('*****WORKING AREA CHOOSE******', filter);
};

dojo.declare('gobotany.sk.working_area.Choice', null, {

    div_map: null,  // maps choice value -> <input> element

    constructor: function(div, filter, species_vector, glossarizer,
                          on_change) {
        this.div = div;
        this.filter = filter;
        this.glossarizer = glossarizer;
        this._draw();
        this.set_species_vector(species_vector);
        this.on_change = on_change;
    },

    /* Draw the working area. */

    _draw_basics: function() {
        var f = this.filter;
        var p = function(s) {return s ? '<p>' + s + '</p>' : s}

        dojo.query('div.working-area h4').html(f.friendly_name);
        dojo.query('div.working-area .question').html(p(f.question));
        dojo.query('div.working-area .hint').html(p(f.hint));
        //dojo.query('div.working-area .actions').html('actions');
        dojo.query('div.working-area').style({display: 'block'});
    },

    _draw: function() {
        var CHOICES_PER_ROW = 5;
        var checked = function(cond) {return cond ? ' checked' : ''};
        var f = this.filter;

        this._draw_basics();

        var values_q = dojo.query('div.working-area .values');
        values_q.empty().addClass('multiple').removeClass('numeric');

        // Apply a custom sort to the filter values.
        var values = gobotany.utils.clone(f.values);
        values.sort(_compare_filter_choices);

        var choices_div = dojo.create('div', {'class': 'choices'}, values_q[0]);
        var row_div = dojo.create('div', {'class': 'row'}, choices_div);

        // Create a Don't Know radio button item.
        this.div_map = {};
        var item_html = '<div><label><input name="char_name"' +
            checked(f.selected_value === null) +
            ' type="radio" value=""> ' + _format_value() + '</label></div>';
        this.div_map[''] = dojo.place(item_html, row_div);

        // Create radio button items for each character value.
        var choices_count = 1;

        for (i = 0; i < values.length; i++) {
            var v = values[i];

            console.log(v, v.choice);
            var item_html = '<label><input name="char_name" type="radio"' +
                checked(f.selected_value === v.choice) +
                ' value="' + v.choice + '">';

            // Add a drawing image thumbnail if present.
            var image_path = v.image_url;
            var thumbnail_html = '';
            var image_id = '';

            if (image_path.length > 0) {
                image_id = this._get_image_id_from_path(image_path);
                thumbnail_html = '<img id="' + image_id +
                    '" src="' + image_path + '" alt="drawing ' +
                    'showing ' + v.friendly_text + '"><br>';
                item_html += thumbnail_html;
            }

            item_html += ' <span class="label">' + _format_value(v) +
                '</span> <span class="count">(n)</span>' +
                '</label>';

            // Start a new row, if necessary, to fit this choice.
            if (choices_count % CHOICES_PER_ROW === 0)
                var row_div = dojo.create(
                    'div', {'class': 'row'}, choices_div);

            choices_count += 1;

            var character_value_div = dojo.create(
                'div', {'innerHTML': item_html}, row_div);
            this.div_map[v.choice] = character_value_div;

            // Once the item is added, add a tooltip for the drawing.
            if (image_path.length > 0) {
                var image_html = '<img id="' + image_id + '" src="' +
                    image_path + '" alt="drawing showing ' +
                    v.friendly_text + '">';
                new dijit.Tooltip({
                    connectId: [image_id],
                    label: image_html, position: ['after', 'above']
                });
            }

            var label = dojo.query('span.label', character_value_div)[0];
            this.glossarizer.markup(label);
        }
    },

    /* Get a value suitable for use as an image element id from the
       image filename found in the image path. */

    _get_image_id_from_path: function(image_path) {
        var last_slash_index = image_path.lastIndexOf('/');
        var dot_index = image_path.indexOf('.', last_slash_index);
        var image_id = image_path.substring(last_slash_index + 1, dot_index);
        return image_id;
    },

    /* Given the vector of species to which all other active filters
       narrow the current pile, compute how many species would remain
       if each possible filter value were applied. */

    set_species_vector: function(species_vector) {
        for (var i = 0; i < this.filter.values.length; i++) {
            var v = this.filter.values[i];
            var vector = gobotany.filters.intersect(species_vector, v.species);
            var count_span_q = dojo.query('.count', this.div_map[v.choice]);
            count_span_q.html('(' + vector.length + ')');
            var input_field_q = dojo.query('input', this.div_map[v.choice]);
            input_field_q.attr('disabled', vector.length === 0);
        }
    }

});

/* Generate a human-readable representation of a value.
 */
var _format_value = function(v) {
    return v === undefined ? "don't know" :
        v.friendly_text ? v.friendly_text :
        v.choice === 'NA' ? "doesn't apply" :
        v.choice ? v.choice : "don't know";
};

/* Order filter choices for display.
 */
var _compare_filter_choices = function(a, b) {

    var friendly_text_a = a.friendly_text.toLowerCase();
    var friendly_text_b = b.friendly_text.toLowerCase();
    var choice_a = a.choice.toLowerCase();
    var choice_b = b.choice.toLowerCase();

    // If both are a number or begin with one, sort numerically.

    var int_friendly_text_a = parseInt(friendly_text_a, 10);
    var int_friendly_text_b = parseInt(friendly_text_b, 10);
    if (!isNaN(int_friendly_text_a) && !isNaN(int_friendly_text_b)) {
        return int_friendly_text_a - int_friendly_text_b;
    }
    var int_choice_a = parseInt(choice_a, 10);
    var int_choice_b = parseInt(choice_b, 10);
    if (!isNaN(int_choice_a) && !isNaN(int_choice_b)) {
        return int_choice_a - int_choice_b;
    }

    // Otherwise, sort alphabetically.

    // Exception: always make Doesn't Apply (NA) last.
    if (choice_a === 'na') return 1;
    if (choice_b === 'na') return -1;

    // If friendly text is present, sort using it.
    if (friendly_text_a < friendly_text_b) return -1;
    if (friendly_text_a > friendly_text_b) return 1;

    // If there is no friendly text, sort using the choices instead.
    if (choice_a < choice_b) return -1;
    if (choice_a > choice_b) return 1;

    return 0; // default value (no sort)
};
