define([
    'jquery',
    'lib/jquery.animate-colors'
], function() {
    var module = {};

    module.bright_change = function($elements, options) {
        options = options || {};
        var start_color = options.start_color || '#ff0';
        var end_color = options.end_color || '#fff';
        $elements.css('background-color', start_color);
        $elements.animate({
            backgroundColor: end_color
        }, 3000, 'linear', function() {
            // When the animation is done, remove the inline style
            // property containing the background color so it will
            // not interfere with future hover or selection states.
            // NOTE: Due to jQuery Ticket #9699 and a bug in Webkit,
            // we set style property to an empty string before
            // deleting it to be sure it's cleared.
            $elements.attr('style', '').removeAttr('style');
        });
    };

    return module;
});
