require([
    'activate_search_suggest',
    'fade',
    'jquery.tools.min'
], function() {
    var FADE_INTERVAL = 6 * 1000; // Includes the fade itself
    setInterval(fade_next_banner_image, FADE_INTERVAL);
});
