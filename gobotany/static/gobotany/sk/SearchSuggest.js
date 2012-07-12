/* Code for a search suggestions menu on the site-wide search box. */

// Configure this module here until we finish the migration
define([
    'dojo/_base/declare',
    'dojox/data/JsonRestStore',
    'dojo/query',
    'dojo/on',
    'dojo/_base/connect',
    'dojo/_base/lang',
    'dojo/keys',
    'dojo/dom',
    'dojo/dom-class',
    'dojo/dom-geometry',
    'dojo/dom-construct',
    'dojo/dom-prop'
],
function(declare, JsonRestStore, query, on, connect, lang, keys,
         dom, domClass, domGeom, domConstruct, domProp) {
return declare('gobotany.sk.SearchSuggest', null, {
    constants: {TIMEOUT_INTERVAL_MS: 200},
    stored_search_box_value: '',
    search_box: null,
    menu: null,
    menu_list: null,
    result_cache: {}, // for caching results for each search queried

    constructor: function(initial_search_box_value) {
        if ((initial_search_box_value !== undefined) &&
            (initial_search_box_value.length)) {
            // The initial search box value (optional) is a value that
            // is expected to be in the search box once the page is
            // initialized. This is to prevent the
            // has_search_box_changed function from detecting a change
            // event when the box is initially populated.
            this.stored_search_box_value = initial_search_box_value;
        }

        this.search_box = query('#search-suggest input')[0];
        if (this.search_box === undefined) {
            console.error('SearchSuggest.js: Search box not found.');
        }

        this.menu = query('#search-suggest .menu')[0];
        if (this.menu === undefined) {
            console.error('SearchSuggest.js: Menu not found.');
        }

        this.menu_list = query('#search-suggest .menu ul')[0];
        if (this.menu_list === undefined) {
            console.error('SearchSuggest.js: Menu list not found.');
        }
    },

    setup: function() {
        // Set up a handler that runs every so often to check for
        // search box changes.
        this.set_timer();

        // Set up keyboard event handlers.
        connect.connect(this.search_box, 'keypress',
            lang.hitch(this, this.handle_keys));

        // Adjust the horizontal position of the menu when the browser
        // window is resized.
        connect.connect(window, 'resize',
            lang.hitch(this, this.set_horizontal_position));
    },

    get_highlighted_menu_item_index: function() {
        var found = false;
        var menu_items = query('li', this.menu);
        var item_index = -1;
        var i = 0;
        while ((found === false) && (i < menu_items.length)) {
            if (domClass.contains(menu_items[i], 'highlighted')) {
                found = true;
                item_index = i;
            }
            i += 1;
        }
        return item_index;
    },

    get_text_from_item_html: function(item_html) {
        // Get the text value of a suggestion from its list item HTML.
        var begin = item_html.indexOf('q=') + 2;
        var end = item_html.indexOf('">');
        var text = item_html.slice(begin, end);
        return text;
    },

    highlight_menu_item: function(item_index) {
        var HIGHLIGHT_CLASS = 'highlighted';

        var menu_item = query('li', this.menu)[item_index];

        if (menu_item !== undefined) {
            // First turn off any already-highlighted item.
            var highlighted_item_index =
                this.get_highlighted_menu_item_index();
            if (highlighted_item_index >= 0) {
                var highlighted_item =
                    query('li', this.menu)[highlighted_item_index];
                domClass.remove(highlighted_item, HIGHLIGHT_CLASS);
            }

            // Highlight the new item.
            domClass.add(menu_item, HIGHLIGHT_CLASS);

            // Put the menu item text in the search box, but
            // first set the stored value so this won't fire a
            // change event.
            var menu_item_text = unescape(
                this.get_text_from_item_html(menu_item.innerHTML));
            this.stored_search_box_value = menu_item_text;
            this.search_box.value = menu_item_text;
        }
        else {
            console.log('menu item ' + item_index + ' undefined');
        }
    },

    highlight_next_menu_item: function() {
        var highlighted_item_index = 
            this.get_highlighted_menu_item_index();
        var next_item_index = highlighted_item_index + 1;
        var num_menu_items = query('li', this.menu).length;
        if (next_item_index >= num_menu_items) {
            next_item_index = 0;
        }
        this.highlight_menu_item(next_item_index);
    },

    highlight_previous_menu_item: function() {
        var highlighted_item_index = 
            this.get_highlighted_menu_item_index();
        var previous_item_index = highlighted_item_index - 1;
        var num_menu_items = query('li', this.menu).length;
        if (previous_item_index < 0) {
            previous_item_index = num_menu_items - 1;
        }
        this.highlight_menu_item(previous_item_index);
    },

    handle_keys: function(e) {
        switch (e.charOrCode) {
            case keys.DOWN_ARROW:
                this.highlight_next_menu_item();
                break;
            case keys.UP_ARROW:
                this.highlight_previous_menu_item();
                break;
            case keys.TAB:
            case keys.ESCAPE:
                this.show_menu(false);
                break;
        }
    },

    set_timer: function(interval_milliseconds) {
        // Set the timer that calls the change-monitoring function.
        // This repeats indefinitely.
        setTimeout(lang.hitch(this, this.check_for_change),
            this.constants.TIMEOUT_INTERVAL_MS);
    },

    check_for_change: function() {
        if (this.has_search_box_changed()) {
            this.handle_search_query();
        }

        // Set the timer again to keep the loop going.
        this.set_timer();
    },

    has_search_box_changed: function() {
        var has_changed = false;

        // See if the current value of the text field differs from
        // what is stored in the instance. Used to decide whether to
        // fetch results.
        if (this.search_box.value !== this.stored_search_box_value) {
            has_changed = true;
            this.stored_search_box_value = this.search_box.value;
        }

        return has_changed;
    },

    set_horizontal_position: function() {
        // Adjust the menu's horizontal position so it lines up with
        // the search box regardless of window width.
        var box_position = domGeom.position(this.search_box, true);
        this.menu.style.left = (box_position.x - 3) + 'px';
    },

    show_menu: function(should_show) {
        var CLASS_NAME = 'hidden';
        if (should_show) {
            domClass.remove(this.menu, CLASS_NAME);
        }
        else {
            domClass.add(this.menu, CLASS_NAME);
        }
        this.set_horizontal_position();
    },

    format_suggestion: function(suggestion, search_query) {
        // Format a suggestion for display.
        return (suggestion = search_query + '<strong>' +
            suggestion.substr(search_query.length) +
            '</strong>').toLowerCase();
    },

    display_suggestions: function(suggestions, search_query) {
        domConstruct.empty(this.menu_list);

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
                var item = domConstruct.create('li');
                domConstruct.create('a',
                    {href: url, innerHTML: label}, item);
                on(item, 'click',
                    lang.hitch(this, this.select_suggestion, item));
                domConstruct.place(item, this.menu_list);
            }
        }
        else {
            this.show_menu(false);
        }
    },

    get_cached_suggestions: function(search_query) {
        return this.result_cache[search_query];
    },

    get_suggestions: function(search_query) {
        var store = new JsonRestStore({target: SUGGEST_URL});
        store.fetch({
            query: {q: search_query},
            scope: this,
            onComplete: function(suggestions) {
                this.result_cache[search_query] = suggestions;
                this.display_suggestions(suggestions, search_query);
            }
        });
    },

    handle_search_query: function() {
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
    },

    select_suggestion: function(list_item) {
        // Go to search results for the item selected.
        var link = query('a', list_item)[0];
        if (link !== undefined) {
            var href = domProp.get(link, 'href');
            if (href !== undefined) {
                var search_string =
                    unescape(href.substring(href.indexOf('=') + 1));
                // Store the search string before updating the search
                // box in order to prevent a change event from firing.
                this.stored_search_box_value = search_string;
                this.search_box.value = search_string;
                this.show_menu(false);
                window.location.href = href;
            }
        }
    }
});
});
