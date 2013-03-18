/* Code for a search suggestions menu on the site-wide search box. */

// Configure this module here until we finish the migration
define([
    'bridge/jquery'
], function($) {

    var TIMEOUT_INTERVAL_MS = 200;
    var keyCode = {
        DOWN: 40,
        UP: 38,
        TAB: 9,
        ESCAPE: 27
    };

    var SearchSuggest = function() {};
    SearchSuggest.prototype = {};

    SearchSuggest.prototype.init = function(initial_search_box_value) {
        // The initial search box value (optional) is a value that
        // is expected to be in the search box once the page is
        // initialized. This is to prevent the
        // has_search_box_changed function from detecting a change
        // event when the box is initially populated.
        this.stored_search_box_value = initial_search_box_value;

        this.search_box = $('#search-suggest input').first();
        this.menu = $('#search-suggest .menu').first();
        this.menu_list = $('#search-suggest .menu ul').first();

        this.result_cache = {};  // for caching results for each search queried
    };

    SearchSuggest.prototype.setup = function() {
        // Set up a handler that runs every so often to check for
        // search box changes.
        this.set_timer();

        // Set up keyboard event handlers.
        this.search_box.keyup($.proxy(this.handle_keys, this));

        // Adjust the horizontal position of the menu when the browser
        // window is resized.
        $(window).resize($.proxy(this.set_horizontal_position, this));
    };

    SearchSuggest.prototype.get_highlighted_menu_item_index = function() {
        var item_index = this.menu.find('li.highlighted').index();

        return item_index;
    };

    SearchSuggest.prototype.get_text_from_item_html = function(item_html) {
        // Get the text value of a suggestion from its list item HTML.
        var begin = item_html.indexOf('q=') + 2;
        var end = item_html.indexOf('">');
        var text = item_html.slice(begin, end);
        return text;
    };

    SearchSuggest.prototype.highlight_menu_item = function(item_index) {
        var HIGHLIGHT_CLASS = 'highlighted';

        var menu_item = this.menu.find('li').eq(item_index);

        if (menu_item !== undefined) {
            // First turn off any already-highlighted item.
            var highlighted_item_index =
                this.get_highlighted_menu_item_index();
            if (highlighted_item_index >= 0) {
                this.menu
                    .find('li')
                    .eq(highlighted_item_index)
                    .removeClass(HIGHLIGHT_CLASS);
            }

            // Highlight the new item.
            menu_item.addClass(HIGHLIGHT_CLASS);

            // Put the menu item text in the search box, but
            // first set the stored value so this won't fire a
            // change event.
            var menu_item_text = unescape(
                this.get_text_from_item_html(menu_item.html()));
            this.stored_search_box_value = menu_item_text;
            this.search_box.val(menu_item_text);
        }
        else {
            console.log('menu item ' + item_index + ' undefined');
        }
    };

    SearchSuggest.prototype.highlight_next_menu_item = function() {
        var highlighted_item_index = 
            this.get_highlighted_menu_item_index();
        var next_item_index = highlighted_item_index + 1;
        var num_menu_items = this.menu.find('li').length;
        if (next_item_index >= num_menu_items) {
            next_item_index = 0;
        }
        this.highlight_menu_item(next_item_index);
    };

    SearchSuggest.prototype.highlight_previous_menu_item = function() {
        var highlighted_item_index = 
            this.get_highlighted_menu_item_index();
        var previous_item_index = highlighted_item_index - 1;
        var num_menu_items = this.menu.find('li').length;
        if (previous_item_index < 0) {
            previous_item_index = num_menu_items - 1;
        }
        this.highlight_menu_item(previous_item_index);
    };

    SearchSuggest.prototype.handle_keys = function(e) {
        switch (e.which) {
            case keyCode.DOWN:
                this.highlight_next_menu_item();
                break;
            case keyCode.UP:
                this.highlight_previous_menu_item();
                break;
            case keyCode.TAB:
            case keyCode.ESCAPE:
                this.show_menu(false);
                break;
        }
    };

    SearchSuggest.prototype.set_timer = function(interval_milliseconds) {
        // Set the timer that calls the change-monitoring function.
        // This repeats indefinitely.
        setTimeout($.proxy(this.check_for_change, this), TIMEOUT_INTERVAL_MS);
    };

    SearchSuggest.prototype.check_for_change = function() {
        if (this.has_search_box_changed()) {
            this.handle_search_query();
        }

        // Set the timer again to keep the loop going.
        this.set_timer();
    };

    SearchSuggest.prototype.has_search_box_changed = function() {
        var has_changed = false;

        // See if the current value of the text field differs from
        // what is stored in the instance. Used to decide whether to
        // fetch results.
        if (this.search_box.val() !== this.stored_search_box_value) {
            has_changed = true;
            this.stored_search_box_value = this.search_box.val();
        }

        return has_changed;
    };

    SearchSuggest.prototype.set_horizontal_position = function() {
        // Adjust the menu's horizontal position so it lines up with
        // the search box regardless of window width.
        var box_position = this.search_box.offset();
        this.menu.css('left', (box_position.left - 3) + 'px');
    };

    SearchSuggest.prototype.show_menu = function(should_show) {
        var CLASS_NAME = 'hidden';
        if (should_show) {
            this.menu.removeClass(CLASS_NAME);
        }
        else {
            this.menu.addClass(CLASS_NAME);
        }
        this.set_horizontal_position();
    };

    SearchSuggest.prototype.format_suggestion = function(
        suggestion, search_query
    ) {
        // Format a suggestion for display.
        return suggestion.replace(new RegExp(search_query, 'i'),
                                  '<span>$&</span>').toLowerCase();
    },

    SearchSuggest.prototype.display_suggestions = function(
        suggestions, search_query
    ) {
        this.menu_list.empty();

        if (suggestions.length > 0) {
            this.show_menu(true);

            var i;
            for (i = 0; i < suggestions.length; i += 1) {
                var suggestion = suggestions[i];
                // Replace any hyphens because the current search
                // configuration does not fully support querying with them.
                var query_value = suggestion.toLowerCase().replace(/\-/g,
                                                                   ' ');
                var url = SEARCH_URL + '?q=' + query_value;
                var label = this.format_suggestion(suggestion,
                    search_query);
                var item = $(document.createElement('li'));
                var link = $(document.createElement('a'));
                link.attr('href', url);
                link.html(label);
                item.append(link);
                item.bind('click', {item: item}, $.proxy(function(event) {
                    this.select_suggestion(event.data.item);
                }, this));
                this.menu_list.append(item);
            }
        }
        else {
            this.show_menu(false);
        }
    };

    SearchSuggest.prototype.get_cached_suggestions = function(search_query) {
        return this.result_cache[search_query];
    };

    SearchSuggest.prototype.get_suggestions = function(search_query) {
        $.ajax({
            url: SUGGEST_URL,
            data: {q: search_query},
            context: this
        }).done(function(suggestions) {
            this.result_cache[search_query] = suggestions;
            this.display_suggestions(suggestions, search_query);
        });
    };

    SearchSuggest.prototype.handle_search_query = function() {
        var search_query = this.stored_search_box_value;
        if (search_query.length > 0) {
            // First check the results cache to see if this value had
            // been queried previously.
            var suggestions = this.get_cached_suggestions(
                search_query);
            if (suggestions === undefined) {
                // Call the server and let the asynchronous response
                // update the display.
                this.get_suggestions(search_query);
            }
            else {
                this.display_suggestions(suggestions, search_query);
            }
        }
        else {
            // Hide the menu because the search box is empty.
            this.show_menu(false);
        }
    };

    SearchSuggest.prototype.select_suggestion = function(list_item) {
        // Go to search results for the item selected.
        var link = list_item.find('a').first();
        if (link !== undefined) {
            var href = link.attr('href');
            if (href !== undefined) {
                var search_string =
                    unescape(href.substring(href.indexOf('=') + 1));
                // Store the search string before updating the search
                // box in order to prevent a change event from firing.
                this.stored_search_box_value = search_string;
                this.search_box.val(search_string);
                this.show_menu(false);
                window.location.href = href;
            }
        }
    };

    return SearchSuggest;
});
