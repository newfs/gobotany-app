// AMD wrapper for underscore library
define('underscore', [
    'tools/underscore-min'
], function(underscore) {
    var module;
    if(window._) {
        // The library is loaded, so return the same
        // underscore object again (the global)
        module = _;
    }

    return module;
});

