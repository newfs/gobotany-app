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
            ENTER: 13,
            SHIFT: 16
        };
        this.SELECTED_CLASS = 'selected';

        this.$input_box = $(input_box);
        this.suggestions_url = this.$input_box.attr('data-suggest-url');
        this.submit_on_select = this.$input_box.attr('data-submit-on-select');
        this.align_menu_inside_input =
            this.$input_box.attr('data-align-menu-inside-input');
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
        var menu_width = this.$input_box.outerWidth(true) - 2;
        if (this.align_menu_inside_input === "true") {
            // If the option to align the menu to the left edge of the
            // padded input box is set, then make the menu narrower too.
            menu_width -= parseInt(this.$input_box.css('padding-right'));
        }
        this.$menu.css('width', menu_width);

        // Position the menu under the box, and adjust the position when
        // the browser window is resized.
        this.set_menu_position();
        $(window).resize($.proxy(this.set_menu_position, this));

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

        // If there is a an empty required field in the form, a validation
        // error shows immediately upon pressing the Enter key (unlike
        // with an HTML5 datalist). This preveted the input box text
        // from updating with the user's selected menu item. In order
        // to overcome this, update the box with the currently selected
        // value as soon as focus leaves the input box.
        this.$input_box.blur($.proxy(this.enter_current_item, this));

        // Hide the menu on focus, such as when tabbing to the field.
        this.$input_box.focus($.proxy(this.hide_menu, this));
    };

    Suggester.prototype.hide_menu = function () {
        this.$menu.hide();
    };

    Suggester.prototype.set_menu_position = function () {
        // Position the menu under the box.
        var $input_box_offset = this.$input_box.offset();
        var input_box_left_padding = 0;
        if (this.align_menu_inside_input === "true") {
            // If the option to align the menu to the inside of a padded
            // input box is set, adjust the left edge position.
            input_box_left_padding +=
                parseInt(this.$input_box.css('padding-left')) - 3;
        }
        this.$menu.css('left',
                       $input_box_offset.left + input_box_left_padding);
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
            case this.KEY_CODE.TAB:
                this.$menu.hide();
                break;
            case this.KEY_CODE.ENTER:
                break;   // Handle only on keydown instead
            case this.KEY_CODE_SHIFT:
                break;   // Prevent menu from appearing when tabbing back
            default:
                this.handle_input_value();
                break;
        }
    };

    Suggester.prototype.handle_keys_down = function (e) {
        // Some things need to be handled on keydown in order to make
        // them work properly.
        switch (e.which) {
            case this.KEY_CODE.TAB:
                this.$menu.hide();
                break;
            case this.KEY_CODE.ENTER:
                // If the menu is visible, prevent the validation and
                // form submit that is normally triggered. This is so
                // the form does not normally submit automatically with
                // an input field with suggestions, matching how HTML5
                // datalists behave.
                if (this.$menu.is(':visible')) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                this.enter_current_item();
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
                                  '<span>$&</span>');
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

                // Handle hovering over the item in a way that truly
                // selects the item rather than using a CSS hover. This
                // is to avoid two items appearing selected at the same
                // time upon traversing the menu first by one input
                // method, then another (such as keyboard, then mouse).
                $item.mouseenter($.proxy(function (e) {
                    this.clear_menu_selection();
                    $(e.target).addClass(this.SELECTED_CLASS);
                }, this));
                $item.mouseleave($.proxy(function (e) {
                    $(e.target).removeClass(this.SELECTED_CLASS);
                }, this));

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

    Suggester.prototype.clear_menu_selection = function () {
        // Un-select any already-selected item.
        this.$menu.find('li').removeClass(this.SELECTED_CLASS);
    };

    Suggester.prototype.select_menu_item = function (item_index) {
        this.clear_menu_selection();
        if (item_index >= 0) {
            var $menu_item = this.$menu.find('li').eq(item_index);
            if ($menu_item !== undefined) {
                $menu_item.addClass(this.SELECTED_CLASS);
            }
        }
    };

    Suggester.prototype.select_next_menu_item = function () {
        if (this.$menu.is(':visible')) {
            var selected_index = this.get_selected_index();
            var next_item_index = selected_index + 1;
            var num_menu_items = this.$menu.find('li').length;
            if (next_item_index > num_menu_items) {
                // Upon scrolling off the bottom of the list, the next Down
                // keypress should select no item, leaving a slot in the
                // sequence for the input box. Then on the next Down keypress,
                // the first item should be selected.
                next_item_index = -1;
            }
            this.select_menu_item(next_item_index);
        }
    };

    Suggester.prototype.select_previous_menu_item = function () {
        if (this.$menu.is(':visible')) {
            var selected_index = this.get_selected_index();
            var previous_item_index = selected_index - 1;
            var num_menu_items = this.$menu.find('li').length;
            if (selected_index <= -1) {
                // Upon scrolling off the top of the list, the next Up
                // keypress should select no item, leaving a slot in the
                // sequence for the input box. Then on the next Up keypress,
                // the last list item should be selected.
                previous_item_index = num_menu_items - 1;
            }
            this.select_menu_item(previous_item_index);
        }
    };

    Suggester.prototype.fill_box = function (value) {
        this.$input_box.val(value);
        this.$menu.hide();

        // If the option to submit the form upon item selection is set,
        // submit the form. This is to support things like single search
        // boxes that should submit right away.
        if (this.submit_on_select === "true") {
            this.$form.submit();
        }
    };

    Suggester.prototype.enter_current_item = function () {
        // Enter the currently selected (highlighted) menu item into
        // the input box.
        var selected_index = this.get_selected_index();
        if (selected_index > -1) {
            var selected_value =
                this.$menu.find('li').eq(selected_index).text();
            this.fill_box(selected_value);
        }
    };

    // Return the constructor function.
    return Suggester;
});
