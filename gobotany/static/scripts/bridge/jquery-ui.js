// AMD wrapper for jquery-ui library.
// This should ensure the AMD loader properly caches jquery
// and only loads it once, and we can be sure that this library
// has jquery loaded before it attempts to load. This also serves
// as a thin abstraction layer so we don't have to worry about
// versioned filenames in our module references.
define([
    'bridge/jquery',
    'jquery/jquery-ui-1.8.16.custom.min'
], function($, ui) {
    var jquery;
    if($.ui) {
        // The plugin is loaded, so return the same
        // jQuery object again (the global)
        jquery = $;
    }

    return jquery;
});

