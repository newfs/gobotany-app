// Google maps API via AMD: http://jasonwyatt.tumblr.com/post/18015760792/
(function () { 
    var callback = function () {},
        callbackName = 'gmapscallback' + (new Date()).getTime();
    window[callbackName] = callback;
    define(['//maps.googleapis.com/maps/api/js?sensor=false&callback=' +
            callbackName], function () {
        return google.maps;
    });
})();
