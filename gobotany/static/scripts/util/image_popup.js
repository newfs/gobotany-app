/* Turn image links into popups that show the image on the same page. */

define([
    'bridge/jquery',
    'util/tooltip'
], function ($, tooltip_js) {

    var module = {};

    // Call this once after document.ready(), to initialize the module.

    module.init = function () {

        module.$shadow = $('<div>').appendTo('#main').addClass('shadow');
        module.$popup = $('<div>').appendTo(module.$shadow).addClass('popup');

        // The popup can be dismissed with the mouse or keyboard.

        module.display_popup = function () {
            module.$shadow.css('display', 'block');
        };
        module.dismiss_popup = function () {
            module.$shadow.css('display', '');
        };
        module.$shadow.on('click', module.dismiss_popup);
        $('body').on('keydown', function (event) {
            if (module.$shadow.css('display') === 'block') { // popup active
                var c = event.which;
                if (c === 13 || c === 27 || c === 32) { // esc, enter, space
                    module.dismiss_popup();
                    return false;
                }
                // PageUp, PageDown, up arrow, down arrow - move whole page
                if (c === 33 || c === 34 || c === 38 || c === 40) {
                    return false;
                }
            }
        });
    };

    // Call this with a CSS selector in order to set up links as popups.
    // Example: image_popup.popup_links('.figure-link');

    module.pop_up_links = function (css_selector) {
        var $elements = $(css_selector);

        $elements.each(function () {
            var $link = $(this);

            var tooltip = new tooltip_js.Tooltip($link, {
                content: $('<p>', {'class': 'glosstip'}).append(
                    $('<img>', {src: $(this).attr('href'), height: 240}),
                    $('<b>', {text: 'Figure ' + $(this).html() + '. '}),
                    $(this).attr('data-caption'),
                    '<br>(Click to view larger image)'
                )
            });

            $link.on('click', function (event) {
                event.preventDefault();
                var $target = $(event.delegateTarget);
                if ($link[0].timeout_id) {
                    clearTimeout($link[0].timeout_id);
                    delete $link[0].timeout_id;
                }
                tooltip.hide_tooltip();
                module.$popup.empty();
                $('<img>').attr('src', $target.attr('href')).appendTo(
                    module.$popup);
                module.display_popup();
            });
        });
    };

    return module;
});
