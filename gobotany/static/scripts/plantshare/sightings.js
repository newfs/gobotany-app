define([
    'bridge/jquery', 
    'util/lazy_images'
], function ($, lazy_images) {

    $(window).load(function () {
        lazy_images.start();
        lazy_images.load();
    });

});
