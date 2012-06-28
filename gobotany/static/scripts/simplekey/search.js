/* Resources that search.html needs. */

require([
    'util/activate_search_suggest',
    'util/sidebar'
], function(activate_search_suggest, sidebar) {
    sidebar.setup()
});
