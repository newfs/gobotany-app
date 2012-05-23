// AMD wrapper for Shadowbox script
define('shadowbox', [
    'tools/shadowbox' 
], function(shadowbox) {
    var module;
    if(window.Shadowbox) {
        // The script is loaded, so return a reference
        // to the global Shadowbox object
        module = window.Shadowbox;
    }

    return module;
});

