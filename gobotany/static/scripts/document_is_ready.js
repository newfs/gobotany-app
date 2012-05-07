define([
    'jquery'
], function() {
    var document_is_ready = $.Deferred();

    $(document).ready(function() {
        document_is_ready.resolve();
    });

    return document_is_ready;
});
