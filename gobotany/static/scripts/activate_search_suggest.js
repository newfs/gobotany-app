require([
    'dojo_config',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js'
], function() {

    dojo.require('gobotany.sk.SearchSuggest');
    dojo.addOnLoad(function() {
        // TODO: Fix this broken constructor string. It is a holdover from
        // when this code existed in a template. It worked there, but it
        // will not work as is once we move the search results page over
        // to the _new_base.html/require.js system.
        var search_suggest = gobotany.sk.SearchSuggest('{{ query }}');
        search_suggest.setup();
    });

});
