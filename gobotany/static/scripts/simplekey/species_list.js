define([

    // Table filtering

    'jquery/picnet.table.filter.min'

], function() {

    $(document).ready(function() {
        var COLUMNS = {
            'name': 0,
            'common': 1,
            'family': 2,
            'dist': 3,
            'native': 4,
            'wetland': 5,
            'group': 6,
            'subgroup': 7
        };

        var SELECTOR_BASE = '#species_filter_';
        var is_initialized = false;
        var filters_to_set_up = {};

        function setup() {
            var filter_selector = SELECTOR_BASE + '0',
                key;
            for (key in filters_to_set_up) {
                if (key in COLUMNS) {
                    filter_selector =  SELECTOR_BASE + COLUMNS[key];
                    // Set the value in the filter's input field.
                    $(filter_selector).val(filters_to_set_up[key]);
                }
                else {
                    console.log('Invalid parameter:', key);
                }
            }
            $('table#species').tableFilterApplyFilterValues();
        }

        function wait_on_init() {
            if ($(SELECTOR_BASE + '0').is(':visible')) {
                is_initialized = true;
            }
            if (is_initialized === false) {
                setTimeout(wait_on_init, 1000);
            }
            else {
                setup();
            }
        }

        // Filter the table.
        var options = {
            enableCookies: false,
            filterDelay: 400
        };
        $('table#species').tableFilter(options);

        // If there are any filters specified on the URL, set them up
        // when the page is ready.
        var hash = decodeURIComponent(window.location.hash);
        if (hash.length > 0) {
            var i, item, items = hash.substr(1).split('&');
            for (i = 0; i < items.length; i++) {
                item = items[i].split('=');
                filters_to_set_up[item[0]] = item[1];
            }
            wait_on_init();
        }

    });

});
