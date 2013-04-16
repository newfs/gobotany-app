define([
    'bridge/jquery',
    'bridge/jquery.cookie',
], function ($, x1) {
    $(document).ready(function () {
        // Set up Cancel button.
        $('.actions .cancel-btn').click(function () {
            window.parent.Shadowbox.close();
        });

        // Set up Delete link.
        var url_parts = window.location.href.split('/');
        var sighting_id = url_parts[url_parts.length - 3];
        var url = url_parts.slice(0, url_parts.length - 2).join('/') + '/';
        var csrf_token = $.cookie('csrftoken');
        
        $('.actions .delete').click(function () {
            $.ajax({
                beforeSend: function(xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrf_token);
                },
                type: "DELETE",
                url: url,
                success: function () {
                    $row = $('#sighting-' + sighting_id,
                             window.parent.document);
                    $row.remove();

                    window.parent.Shadowbox.close();
                }
            });
            return false;
        });
    });
});
