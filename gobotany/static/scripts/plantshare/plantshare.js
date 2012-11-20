define([
    'bridge/jquery'
], function ($) {

    $(document).ready(function () {

        //console.log('Hello, this is plantshare.js calling');

        $('#sightings-locator form').submit(function (e) {
            e.preventDefault();   // prevent form submit

            console.log('TODO: call the server for sightings data');
        });

    });
});
