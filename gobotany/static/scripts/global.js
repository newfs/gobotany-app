// TODO: Integrate all this code into an appropriate place within the
// main JavaScript code base, and get rid of this file.

define(['jquery.tools.min'], function() {

// Animate and position the Shadowbox close link.
global_moveShadowboxCloseLink = function() {
    var cb = document.getElementById('sb-nav-close');
    var tb = document.getElementById('sb-wrapper');
    if (tb) {
        tb.appendChild(cb);
    }
};

});
