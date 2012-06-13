// AMD wrapper for picnet-table-filter plugin.
// This should ensure the AMD loader properly caches jquery
// and only loads it once, and we can be sure that this plugin
// has jquery loaded before it attempts to load. This also serves
// as a thin abstraction layer so we don't have to worry about
// versioned filenames in our module references.
define([
    'bridge/jquery', 
    'jquery/picnet.table.filter.min'
], function($, picnettablefilter) {
    var jquery;
    if($.fn.tableFilter) {
        // The plugin is loaded, so return the same
        // jQuery object again (the global)
        jquery = $;
    }

    return jquery;
});


