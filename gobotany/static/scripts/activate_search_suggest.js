// JQuery is included here for documentation purposes
// but AMD support is minimal at this point so we're
// still using the global object
require([
    'dojo/ready',
    'jquery.tools.min',
    'simplekey/resources',
    'gobotany/sk/SearchSuggest'
], function(ready, jquery, resources, SearchSuggest) {
    return ready(function() {
        var initial_search_box_value = $('#search input').val();
        var search_suggest = SearchSuggest(initial_search_box_value);
        search_suggest.setup();
    });
});
