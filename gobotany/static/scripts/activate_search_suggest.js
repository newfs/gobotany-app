require([
    'dojo_config',
    'simplekey/resources',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js'
], function() {

    dojo.require('gobotany.sk.SearchSuggest');
    dojo.addOnLoad(function() {
        var search_suggest = gobotany.sk.SearchSuggest();
        search_suggest.setup();
    });

});
