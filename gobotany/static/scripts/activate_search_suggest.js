require([
    'order!dojo_config',
    'order!/static/js/dojo/dojo.js',
    'simplekey/resources'
], function() {
    
    require([
        '/static/js/layers/sk.js'
    ], function() {

        dojo.require('gobotany.sk.SearchSuggest');
        dojo.addOnLoad(function() {
            var initial_search_box_value = $('#search input').val();
            var search_suggest = gobotany.sk.SearchSuggest(
                initial_search_box_value);
            search_suggest.setup();
        });
    });

});
