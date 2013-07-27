require([
    'util/fade'
], function(fade_next_banner_image) {
    var FADE_INTERVAL = 15 * 1000; // Includes the fade itself
    setInterval(fade_next_banner_image, FADE_INTERVAL);
});
