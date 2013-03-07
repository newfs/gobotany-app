/*
 * The most basic working-area class, which the other versions of the class
 * inherit from and specialize, is the standard multiple-choice selection.
 */
define([
    'bridge/jquery',
    'bridge/underscore',
    'simplekey/App3',
    'simplekey/utils',
    'util/glossarizer',
    'util/tooltip'
], function($, _, App3, utils, glossarizer, tooltip) {

    var glossarize = glossarizer.glossarize;

    /* Generate a human-readable representation of a value. */

    var _format_value = function(v) {
        return v === undefined ? "don't know" :
            v.friendly_text ? v.friendly_text :
            v.choice === 'NA' ? "doesn't apply" :
            v.choice ? v.choice : "don't know";
    };

    /* Order filter choices for display. */

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

    /* Choice objects */

    var Choice = function() {};
    Choice.prototype = {};

    Choice.prototype.init = function(args) {
        this.div = args.div;
        this.div_map = null,   // map choice value -> <input> element
        this.filter = args.filter;
        this.max_smallscreen_width = args.max_smallscreen_width;
        this.glossarize_mobile = args.glossarize_mobile;
        this.terms_section = args.terms_section;

        this._attach();
        this._draw_basics(args.y);
        this._draw_specifics();
        this._on_filter_change();
    };

    /* Events that can be triggered from outside. */

    Choice.prototype.clear = function() {
        $('input', this.div_map['']).prop('checked', true);
    };

    Choice.prototype.dismiss = function(e) {
        if (e) {
            e.preventDefault();
        }

        $('.close', this.div).unbind();
        $('.apply-btn', this.div).unbind();

        $(this.div).hide();

        $('.option-list li').removeClass('active');
    };

    /* Draw the working area. */

    Choice.prototype._draw_basics = function(y) {
        var $div = $(this.div);
        var f = this.filter;
        var p = function(s) {return s ? '<p>' + s + '</p>' : s}

        // Reset the small-screens glossary terms section.
        $(this.terms_section).addClass('none');
        $(this.terms_section).find('ul').empty();

        // Show the question, hint and Apply button.
        
        var $question = $div.find('.question');
        var $hint = $div.find('.hint');
        var $info_section = $div.find('.info');

        $question.html(f.info.question);
        $hint.html(p(f.info.hint));

        if ($(window).width() > this.max_smallscreen_width) {
            glossarize($question);
            glossarize($hint.find('p'));
        }
        else if (this.glossarize_mobile) {
            // List glossary terms in a separate section on small screens.
            glossarize($question, this.terms_section);
            glossarize($hint.find('p'), this.terms_section);
        }
        
        $question.css('display', 'block');
        $info_section.css('display', 'block');

        // Display character drawing, if an image is available.
        if (f.info.image_url) {
            var image_id = this._get_image_id_from_path(f.info.image_url);
            var character_drawing_html = '<img id="' + image_id +
                '" src="' + f.info.image_url +
                '" alt="character illustration">';
            $div.find('.character-drawing').html(character_drawing_html).css(
                {display: 'block'});
        } else {
            $div.find('.character-drawing').html('').css({display: 'none'});
        }

        // Show the working area with a slide effect.
        $div.css('top', y + 'px').slideDown('fast');

        // Hook up the Close button.
        $('.close', this.div).bind(
            'click', $.proxy(this, 'dismiss'));

        // Hook up the Apply button.
        $('.apply-btn', this.div).bind(
            'click', $.proxy(this, '_apply_button_clicked'));
    };

    Choice.prototype._draw_specifics = function() {
        var BLANK_IMAGE = '/static/images/layout/transparent.png';
        var CHOICES_PER_ROW = 5;
        var choices_class = 'choices';
        var checked = function(cond) {return cond ? ' checked' : ''};
        var f = this.filter;

        var $div = $('div.working-area .values');
        $div.empty().addClass('multiple').removeClass('numeric');

        // Apply a custom sort to the filter values.
        var values = utils.clone(f.values);
        values.sort(_compare_filter_choices);

        // Find out whether there are any drawing images for this filter.
        var has_drawings = false;
        for (var i = 0; i < values.length; i++) {
            var image_path = values[i].image_url;
            if (image_path.length > 0) {
                has_drawings = true;
                choices_class += ' has-drawings';
                break;
           }
        }

        // Create the container for the choices.
        var $choices = $('<div>', {'class': choices_class}).appendTo($div);
        var $row = $('<div>', {'class': 'row'}).appendTo($choices);

        // Create a Don't Know radio button item.
        var item_html = '<div class="choice' +
            checked(f.value === null) + '">';
        if (has_drawings === true) {
            // Include a blank image to keep the layout intact.
            item_html += '<div class="drawing"><img ' + 
            'src="' + BLANK_IMAGE + '" ' +
            'alt=""></div>';
        }
        item_html += '<label><input name="char_name"' +
            checked(f.value === null) +
            ' type="radio" value=""> <span class="choice-label">' +
            _format_value() + '</span></label></div>';

        this.div_map = {};
        this.div_map[''] = $(item_html).appendTo($row)[0];

        // Create radio button items for each character value.
        var choices_count = 1;

        for (i = 0; i < values.length; i++) {
            var v = values[i];

            var item_html = '<div class="choice' +
                checked(f.value === v.choice) + '">';

            if (has_drawings === true) {
                // Add a drawing image if present. If there is no drawing,
                // add a blank image to keep the layout intact.
                item_html += '<div class="drawing">';
                var image_path = v.image_url;
                if (image_path.length > 0) {
                    var image_id = this._get_image_id_from_path(image_path);
                    item_html += '<img id="' + image_id +
                        '" src="' + image_path + '" alt="drawing ' +
                        'showing ' + v.friendly_text + '">';
                }
                else {
                    item_html += '<img src="' + BLANK_IMAGE + '" alt="">';
                }
                item_html += '</div>';
            }

            item_html += '<label><input name="char_name" type="radio"' +
                checked(f.value === v.choice) +
                ' value="' + v.choice + '">';

            item_html += ' <span class="choice-label"><span class="label">' +
                _format_value(v) + '</span> <span class="count">(n)</span>' +
                '</span></label>';

            // Start a new row, if necessary, to fit this choice.
            if (choices_count % CHOICES_PER_ROW === 0)
                var $row = $('<div>', {'class': 'row'}).appendTo($choices);

            choices_count += 1;

            var character_value_div = $(item_html).appendTo($row)[0];
            this.div_map[v.choice] = character_value_div;

            // Once the item is added, add a tooltip for the drawing.
            if (image_path.length > 0) {
                var image_html = '<img class="char-value-larger" id="' +
                    image_id + '" src="' + image_path +
                    '" alt="drawing showing ' + v.friendly_text + '">';
                var $image = $('#' + image_id);
                $image.tooltip({
                    content: image_html,
                    width: 'auto'
                });

                // Make clicking the drawing select the choice if available.
                $image.bind('click', function () {
                    $radio = $(this).closest('.choice').find('input').eq(0);
                    var $disabled = $radio.attr('disabled');
                    if (typeof $disabled === 'undefined' ||
                        $disabled === false) {
                        $radio.attr('checked', 'true');
                        $radio.trigger('click');
                    }
                });
            }

            if ($(window).width() > this.max_smallscreen_width) {
                glossarize($('span.label', character_value_div));
            }
            else if (this.glossarize_mobile) {
                // List glossary terms in a separate section on small screens.
                glossarizer.glossarize($('span.label', character_value_div),
                                       this.terms_section);
            }
        }

        // Call a method when radio button is clicked.
        $div.find('input').bind('click', $.proxy(this, '_on_choice_change'));

        // Set up the Apply Selection button.
        this._on_choice_change();
    };

    /* Place the working-area element after the selected filter so that it
       will be possible to allow displaying filter values "inline." */
    
    Choice.prototype._attach = function() {
        var $filter_list_item = $('#questions-go-here ul #' +
                                  this.filter.slug);
        $(this.div).appendTo($filter_list_item);
    };

    /* How to grab the currently-selected value from the DOM. */

    Choice.prototype._current_value = function() {
        var value = $('input:checked', this.div).attr('value');
        return value || null;
    };

    /* Update some aspects of the working area when the choice changes. */

    Choice.prototype._on_choice_change = function(e) {
        // Set a class of "selected" on the now-selected choice.
        $('.choice', this.div).each(function() {
            $(this).removeClass('checked');
        });
        var $checked_input = $('input:checked', this.div);
        $checked_input.closest('.choice').addClass('checked');

        // Update whether the "Apply Selection" button is gray or not.
        var $apply_button = $('.apply-btn', this.div);
        if (this._current_value() === this.filter.value)
            $apply_button.addClass('disabled');
        else
            $apply_button.removeClass('disabled');
    };

    /* Get a value suitable for use as an image element id from the
       image filename found in the image path. */

    Choice.prototype._get_image_id_from_path = function(image_path) {
        var last_slash_index = image_path.lastIndexOf('/');
        var dot_index = image_path.indexOf('.', last_slash_index);
        var image_id = image_path.substring(last_slash_index + 1, dot_index);
        return image_id;
    };

    /* When the set of selected filters changes, we need to recompute
       how many species would remain if each of our possible filter
       values were applied. */

    Choice.prototype._on_filter_change = function() {
        var other_taxa = App3.filter_controller.compute(this.filter);
        var div_map = this.div_map;

        _.map(this.filter.values, function(value) {

            // How many taxa would be left if this value were chosen?
            var num_taxa = _.intersection(value.taxa, other_taxa).length;

            // Draw it accordingly.
            var div = div_map[value.choice];
            var $count_span = $('.count', div);
            $count_span.html('(' + num_taxa + ')');
            var $input_field = $('input', div);
            if (num_taxa === 0) {
                $(div).addClass('disabled');
                $input_field.attr('disabled', 'disabled');
            } else {
                $(div).removeClass('disabled');
                $input_field.attr('disabled', false); // remove the attribute
            }
        });
    };

    /* When the apply button is pressed, we announce a value change
       unless it would bring the number of species to zero. */

    Choice.prototype._apply_button_clicked = function(e) {
        var apply_button = $('.apply-btn');
        if (apply_button.hasClass('disabled'))
            return false;
        apply_button.removeClass('disabled');
        this._apply_filter_value();
        this.dismiss();
        
        if ($(window).width() <= this.max_smallscreen_width) {
            $('#question-nav').addClass('closed'); // Collapse questions list

            // Scroll to the top of the page and then just to the relevant
            // navigation in order to be sure the results count is visible,
            // and to trigger lazy image loading if photos are shown.
            window.scrollTo(0, 0);
            window.scrollTo(0, 90);
        }
        
        return false;
    };

    Choice.prototype._apply_filter_value = function() {
        var value = this._current_value();
        if (value !== null && this.filter.taxa_matching(value).length == 0)
            // Refuse to let the number of matching taxa be driven to zero.
            return;
        this.filter.set('value', value);
    };

    return Choice;
});
