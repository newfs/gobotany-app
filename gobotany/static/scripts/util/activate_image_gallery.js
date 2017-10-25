/*
 * Activate any class="img-container" elements to make them scrollable
 * using their "prev" and "next" buttons.
 */

require([
    'bridge/jquery',
    'util/ImageGallery'
], function ($, ImageGallery) {

    $(document).ready(function () {
        var image_gallery = new ImageGallery();
        image_gallery.activate();
    });
});
