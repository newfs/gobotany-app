/* Support showing a list of suggestions for a text input field. */

define([
    'bridge/jquery'
], function ($) {

    function Suggester(input_box) {
        // Constructor
        
        this.TIMEOUT_INTERVAL_MS = 200;
        this.KEY_CODE = {
            DOWN: 40,
            UP: 38,
            TAB: 9,
            ESCAPE: 27,
            ENTER: 13
        };
        this.SELECTED_CLASS = 'selected';

        this.$input_box = $(input_box);
        this.suggestions_url = this.$input_box.attr('data-suggest-url');
        this.cached_suggestions = {};
    };

    Suggester.prototype.setup = function () {
        this.$form = this.$input_box.parent(); // TODO: more reliable way
                                               // in case form fields
                                               // are wrapped in divs

        // Add an element for the suggestions menu.
        this.$input_box.after('<div><ul></ul></div>');

        this.$menu = this.$input_box.next();
        this.$menu.hide();

        this.$menu_list = this.$menu.children('ul').eq(0);

        // Set the width of the menu to match that of the box.
        this.$menu.css('width', this.$input_box.outerWidth(true) - 2);

        // Position the menu under the box, and adjust the position when
        // the browser window is resized.
        this.set_menu_position();
        $(window).resize($.proxy(this.set_menu_position, this));

        // Prevent automatically submitting the form upon pressing Enter
        // for this form, now that it contains an input box with
        // suggestions. This should be OK, at least in most cases.
        this.$form.submit($.proxy(this.prevent_submit_on_menu_enter, this));

        // Set up keyboard event handlers.
        this.$input_box.keyup($.proxy(this.handle_keys_up, this));
        this.$input_box.keydown($.proxy(this.handle_keys_down, this));

        // Hide the menu upon clicking outside the input box.
        $(document).click($.proxy(
            function () {
                this.$menu.hide();
            }, this)
        );
        this.$menu.click(function (event) {
            event.stopPropagation();
        });
    };

    Suggester.prototype.prevent_submit_on_menu_enter = function (e) {
        // If the menu is visible, prevent the form from submitting 
        // automatically upon pressing the Enter key in order to make
        // these input boxes behave like HTML5 datalists (and
        // combo-boxes elsewhere).
        if (this.$menu.is(':visible')) {
            e.preventDefault();
        }
    };

    Suggester.prototype.set_menu_position = function () {
        // Position the menu under the box.
        var $input_box_offset = this.$input_box.offset();
        this.$menu.css('left', $input_box_offset.left);
        this.$menu.css('top',
                       $input_box_offset.top + this.$input_box.outerHeight());
    };

    Suggester.prototype.handle_keys_up = function (e) {
        switch (e.which) {
            case this.KEY_CODE.DOWN:
                this.select_next_menu_item();
                break;
            case this.KEY_CODE.UP:
                this.select_previous_menu_item();
                break;
            case this.KEY_CODE.ESCAPE:
                this.$menu.hide();
                break;
            case this.KEY_CODE.ENTER:
                this.enter_current_item();
                this.$menu.hide();
                break;
            default:
                this.handle_input_value();
                break;
        }
    };

    Suggester.prototype.handle_keys_down = function (e) {
        switch (e.which) {
            case this.KEY_CODE.TAB:
                this.$menu.hide();
                break;
        }
    };

    Suggester.prototype.handle_input_value = function () {
        var input_value = this.$input_box.val();
        if (input_value.length > 0) {
            // First check the results cache to see if this value had
            // been queried previously.
            var suggestions = this.cached_suggestions[input_value];
            if (suggestions === undefined) {
                // Suggestions are not in the cache. Call the server and
                // let the asynchronous response update the display.
                this.get_suggestions(input_value);
            }
            else {
                // Display suggestions retrieved from the cache.
                this.display_suggestions(suggestions, input_value);
            }
        }
        else {
            // Hide the menu because the search box is empty.
            this.$menu.hide();
        }
    };

    Suggester.prototype.get_suggestions = function (input_value) {
        var url = this.suggestions_url.replace('%s', input_value);
        $.ajax({
            url: url,
            context: this
        }).done(function (suggestions) {
            this.cached_suggestions[input_value] = suggestions;
            this.display_suggestions(suggestions, input_value);
        });
    };

    Suggester.prototype.format_suggestion = function (suggestion,
                                                      input_value) {
        // Format a suggestion for display.
        return suggestion.replace(new RegExp(input_value, 'i'),
                                  '<span>$&</span>').toLowerCase();
    };

    Suggester.prototype.display_suggestions = function (suggestions,
                                                        input_value) {
        this.$menu_list.empty();

        if (suggestions.length > 0) {
            this.$menu.show();

            var i;
            for (i = 0; i < suggestions.length; i += 1) {
                var suggestion = suggestions[i];

                // Replace any hyphens because the current search
                // configuration does not fully support querying with them.
                // TODO: probably do this elsewhere given use beyond search
                var query_value = suggestion.toLowerCase().replace(/\-/g,
                                                                   ' ');
                var label = this.format_suggestion(suggestion, input_value);
                var $item = $(document.createElement('li'));
                $item.append(label);

                // Bind an event to activate the item with a click or tap.
                $item.click($.proxy(function (e) {
                    var selected_value = e.target.innerText;
                    this.fill_box(selected_value);
                }, this));
                
                this.$menu_list.append($item);
            }
        }
        else {
            this.$menu.hide();
        }
    };

    Suggester.prototype.get_selected_index = function () {
        return this.$menu.find('li.' + this.SELECTED_CLASS).index();
    };

    Suggester.prototype.select_menu_item = function (item_index) {
        var $menu_item = this.$menu.find('li').eq(item_index);

        if ($menu_item !== undefined) {
            // First un-select any already-selected item.
            var selected_index = this.get_selected_index();
            if (selected_index >= 0) {
                var $selected_item = this.$menu.find('li').eq(selected_index);
                $selected_item.removeClass(this.SELECTED_CLASS);
            }

            // Select the new item.
            $menu_item.addClass(this.SELECTED_CLASS);
        }
        else {
            console.log('$menu item ' + item_index + ' undefined');
        }
    };

    Suggester.prototype.select_next_menu_item = function () {
        var selected_index = this.get_selected_index();
        var next_item_index = selected_index + 1;
        var num_menu_items = this.$menu.find('li').length;
        if (next_item_index >= num_menu_items) {
            next_item_index = 0;
        }
        this.select_menu_item(next_item_index);
    };

    Suggester.prototype.select_previous_menu_item = function () {
        var selected_index = this.get_selected_index();
        var previous_item_index = selected_index - 1;
        var num_menu_items = this.$menu.find('li').length;
        if (previous_item_index < 0) {
            previous_item_index = num_menu_items - 1;
        }
        this.select_menu_item(previous_item_index);
    };

    Suggester.prototype.fill_box = function (value) {
        this.$input_box.val(value);
        this.$menu.hide();

        // If there is only one non-hidden form element in the form,
        // submit the form. This is to support use for things like
        // single search boxes that should submit right away.
        var $non_hidden_form_elements = this.$form.find(
            'input:not([type=hidden]), select, textarea');
        if ($non_hidden_form_elements.length === 1) {
            this.$form.submit();
        }
    };

    Suggester.prototype.enter_current_item = function (e) {
        // Enter the currently selected (highlighted) menu item into
        // the input box.
        var selected_index = this.get_selected_index();
        var selected_value = this.$menu.find('li').eq(selected_index).text();
        this.fill_box(selected_value);
    };

    // Return the constructor function.
    return Suggester;
});
