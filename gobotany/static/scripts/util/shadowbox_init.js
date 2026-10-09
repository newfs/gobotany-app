/* Make a few global customizations to Shadowbox initialization. */

define([
    'bridge/jquery', 
    'bridge/shadowbox'
], function ($, Shadowbox) {

    // Animate and position the close button, and set up keyboard handlers.
    shadowbox_move_close_button = function () {
        var cb = document.getElementById('sb-nav-close');
        var tb = document.getElementById('sb-wrapper');
        let interactiveElements;
        let firstInteractiveElement;
        let lastInteractiveElement;
        if (cb) {
            if (tb) {
                // Move the close box node to the end, the last node.
                tb.appendChild(cb);

                // Get the interactive elements in the dialog.
                interactiveElements = tb.querySelectorAll('span.gloss, button, a');
                if (interactiveElements.length) {
                    firstInteractiveElement = interactiveElements[0];
                    lastInteractiveElement = interactiveElements[
                        interactiveElements.length - 1];
                }
            }
            if (firstInteractiveElement) {
                firstInteractiveElement.addEventListener('keydown', function (event) {
                    if (event.shiftKey && event.key === 'Tab') { // Shift-Tab
                        // Set focus to last interactive element.
                        if (lastInteractiveElement) {
                            lastInteractiveElement.focus();

                            // Prevent this Shift-Tab event from moving one prior.
                            event.preventDefault();
                        }
                    }
                });
            }

            // If the modal dialog's included close button is shown, it should
            // be the last element.
            cb.setAttribute('role', 'button');
            cb.setAttribute('href', 'javascript:void(0);');
            cb.addEventListener('keydown', function (event) {
                if (event.key === ' ') {   // Space key
                    event.preventDefault();
                    event.target.click();
                }
                else if (event.key === 'Tab' && !event.shiftKey) { // Tab
                    if (tb) {
                        if (firstInteractiveElement) {
                            firstInteractiveElement.focus();

                            // Prevent this Tab event from moving one after.
                            event.preventDefault();
                        }
                    }
                }
            });

            // Set initial focus on the close button.
            cb.focus();
        }
    };

    shadowbox_on_open = function () {
        // Prevent the page background from scrolling.
        document.body.style.overflow = 'hidden';

        // Move the close button and set up keyboard handlers after a delay
        // to let the contents load.
        setTimeout(function () {
            shadowbox_move_close_button();
        }, 1500);
    };

    shadowbox_on_close = function () {
        // Allow the page background to scroll again.
        document.body.style.overflow = 'unset';

        // Hide any tooltips activated from the lightbox.
        $('.gb-tooltip.dark').hide();
    };

    $(document).ready(function () {
        Shadowbox.init({
            onClose: shadowbox_on_close,
            onOpen: shadowbox_on_open,
            overlayOpacity: 0.8,
            viewportPadding: 0
        });
    });

    /* Return Shadowbox as a convenience, so users do not have to import
       both Shadowbox and shadowbox_init themselves. */

    return Shadowbox;
});
