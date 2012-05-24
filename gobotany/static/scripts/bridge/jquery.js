// Name this module so the AMD loader knows how to cache it properly.
define([
    'jquery/jquery.tools.min'
], function(jquery) {
    // jQuery loads itself into the global namespace by default, so
    // to be a bit more AMD-like and return that same global jQuery
    // object as the value of this AMD wrapper module.

    // If this isn't true, jquery hasn't been loaded globally
    if(window.$) {
        jquery = window.$;
    }
    return jquery;
});
