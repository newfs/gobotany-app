// AMD wrapper for JS JPEG Meta script
// (https://github.com/bennoleslie/jsjpegmeta)
define([
    'lib/jpegmeta'
], function (jpegmeta) {
    var module;
    if (window.JpegMeta) {
        // The script is loaded, so return a reference
        // to the global JpegMeta object
        module = window.JpegMeta;
    }

    return module;
});
