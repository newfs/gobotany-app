require([
    'util/activate_search_suggest',
    'util/fade'
], function(activate_search_suggest, fade_next_banner_image) {
    var FADE_INTERVAL = 6 * 1000; // Includes the fade itself
    setInterval(fade_next_banner_image, FADE_INTERVAL);
});
