dojo.provide('gobotany.sk.SearchSuggest');

dojo.require('dojox.data.JsonRestStore');

dojo.declare('gobotany.sk.SearchSuggest', null, {
    constants: { TIMEOUT_INTERVAL_MS: 500, },
    stored_search_box_value: '',
    search_box: null,
    menu: null,
    menu_list: null,
    result_cache: {},   // for caching results for each search string queried

    constructor: function(initial_search_box_value) {
        if ((initial_search_box_value !== undefined) &&
            (initial_search_box_value.length)) {
            // The initial search box value (optional) is a value that is
            // expected to be in the search box once the page is initialized.
            // This is to prevent the has_search_box_changed function from
            // detecting a change event when the box is initially populated.
            this.stored_search_box_value = initial_search_box_value;
        }

        this.search_box = dojo.query('#search-suggest input')[0];
        if (this.search_box === undefined) {
            console.error('SearchSuggest.js: Search box not found.');
        }

        this.menu = dojo.query('#search-suggest div')[0];
        if (this.menu === undefined) {
            console.error('SearchSuggest.js: Menu not found.');
        }

        this.menu_list = dojo.query('#search-suggest div ul')[0];
        if (this.menu_list === undefined) {
            console.error('SearchSuggest.js: Menu list not found.');
        }
    },

    setup: function() {
        // Set up a handler that runs every so often to check for search
        // box changes.
        this.set_timer();
    },
    
    set_timer: function(interval_milliseconds) {
        // Set the timer that calls the change-monitoring function. This must
        // be called again every time the function runs in order for it to
        // repeat indefinitely.
        setTimeout(dojo.hitch(this, this.check_for_change),
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

        // See if the current value of the text field differs from what is
        // stored in the instance. Used to decide whether to fetch results.
        if (this.search_box.value !== this.stored_search_box_value) {
            has_changed = true;
            this.stored_search_box_value = this.search_box.value;
        }

        return has_changed;
    },
    
    show_menu: function(should_show) {
        var CLASS_NAME = 'hidden';
        if (should_show) {
            dojo.removeClass(this.menu, CLASS_NAME);
        }
        else {
            dojo.addClass(this.menu, CLASS_NAME);
        }
    },

    format_suggestion: function(suggestion, search_query) {
        // Format a suggestion for display.
        return (suggestion = search_query + '<strong>' +
            suggestion.substr(search_query.length) +
            '</strong>').toLowerCase();
    },

    display_suggestions: function(suggestions, search_query) {
        dojo.empty(this.menu_list);

        if (suggestions.length > 0) {
            this.show_menu(true);

            for (var i = 0; i < suggestions.length; i++) {
                var suggestion = suggestions[i];
                var url = '/simple/search/?q=' + suggestion.toLowerCase();
                var label = this.format_suggestion(suggestion, search_query);
                var item = dojo.create('li');
                var link = dojo.create('a', { href: url,
                                              innerHTML: label,
                                            }, item);
                dojo.connect(item, 'onclick',
                    dojo.hitch(this, this.select_suggestion, item));
                dojo.place(item, this.menu_list);
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
        var SUGGEST_URL = '/simple/suggest/';
        var store = new dojox.data.JsonRestStore({target: SUGGEST_URL});
        store.fetch({
            query: { q: search_query },
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
            // First check the results cache to see if this value had been
            // queried previously.
            var suggestions = this.get_cached_suggestions(search_query);
            if (suggestions === undefined) {
                // Call the server and let the asynchronous response update
                // the display.
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
        var link = dojo.query('a', list_item)[0];
        if (link !== undefined) {
            var href = dojo.attr(link, 'href');
            if (href !== undefined) {
                var search_string =
                    unescape(href.substring(href.indexOf('=') + 1));
                // Store the search string before updating the search box in
                // order to prevent a change event from firing.
                this.stored_search_box_value = search_string;
                this.search_box.value = search_string;
                dojo.addClass(this.menu, 'hidden');
                window.location.href = href;
            }
        }
    },

});
