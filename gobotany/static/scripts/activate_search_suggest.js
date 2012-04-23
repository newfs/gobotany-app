require([
    'dojo/ready',
    'jquery.tools.min',
    'simplekey/resources',
    'gobotany/sk/SearchSuggest'
], function(ready, $, resources, SearchSuggest) {
    ready(function() {
        var initial_search_box_value = $('#search input').val();
        var search_suggest = SearchSuggest(
            initial_search_box_value);
        search_suggest.setup();
    });
});
