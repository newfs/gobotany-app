/*
 * Activate any class="img-container" elements to make them scrollable
 * using their "prev" and "next" buttons.
 */

require([
    'jquery.tools.min',
    'jquery.mousewheel.min'
], function() {

    $(document).ready(function() {
        $('.img-container').scrollable({keyboard: false});
    });

});
