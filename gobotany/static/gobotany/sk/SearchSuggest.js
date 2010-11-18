dojo.provide('gobotany.sk.SearchSuggest');

dojo.declare('gobotany.sk.SearchSuggest', null, {
    constants: { TIMEOUT_INTERVAL_MS: 500, },
    stored_search_box_value: '',
    search_box: null,
    menu: null,
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
    },

    setup: function() {
        // Set up the search box suggestion feature.

        // Set up a handler that runs every so often to check for search
        // box changes.
        this.set_timer();

        // For now, attach a click handler to each of the dummy
        // suggestions here. Later will need to attach this on the fly
        // whenever new suggestions are placed in the box.
        var list_items = dojo.query('#search-suggest li');
        for (var i = 0; i < list_items.length; i++) {
            dojo.connect(list_items[i], 'onclick', 
                dojo.hitch(this, this.select_suggestion, list_items[i]));
        }

    },
    
    set_timer: function(interval_milliseconds) {
        // Set the timer that calls the change-monitoring function. This must
        // be called again every time the function runs in order for it to
        // repeat indefinitely.
        setTimeout(dojo.hitch(this, this.check_for_change),
            this.constants.TIMEOUT_INTERVAL_MS);
    },

    check_for_change: function() {
        //console.log('check_for_change');
        if (this.has_search_box_changed()) {
            this.update_menu_visibility();
            this.handle_search_query();
        }
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
    
    update_menu_visibility: function() {
        if (this.stored_search_box_value === '') {
            // When the search box is empty, hide the menu.
            this.show_menu(false);
        }
        else {
            this.show_menu(true);
        }
    },

    handle_search_query: function() {
        console.log('handle_search_query: ' + this.stored_search_box_value);
        
        // TODO:
        // First check the results cache to see if this value had been queried
        // previously.
        //
        // If not in the cache, issue a request to the server.
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
