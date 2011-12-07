require([
    'dojo_config',
    'simplekey/resources',
    '/static/js/dojo/dojo.js',
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
