require([
    'bridge/jquery',
    'gobotany/sk/SearchSuggest'
], function($, SearchSuggest) {
    return $(document).ready(function() {
        var initial_search_box_value = $('#search input').val();
        var search_suggest = new SearchSuggest();
        search_suggest.init(initial_search_box_value);
        search_suggest.setup();
    });
});
