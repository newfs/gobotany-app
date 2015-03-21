/* Redirect the old question URL format to the current one:
 * /questions/all/#q{id} --> /questions/all/{year}/#q{id}
 * This is
 * done on the client side because fragment identifiers (# hashes)
 * do not get sent to the server side.
 */

define([
    'bridge/jquery'
], function ($) {

    $(document).ready(function () {

        // Only consider redirecting if the URL has no year on the end
        // and a hash is present.
        var no_year = window.location.href.toString().split('#')[0].endsWith(
            '/all/');
        if (no_year && window.location.hash) {
            // Check if there's a matching id in this page. If not,
            // redirect to let the server figure out the final URL.
            var hash = window.location.hash.split('?')[0];
            var found = $(hash);
            if (found.length === 0) {
                var parts = hash.split('q');
                var question_id = parts[1];
                if (question_id.length > 0) {
                    var url = '/plantshare/questions/all/?q=' + question_id +
                        '#q' + question_id;
                    // Redirect to the server side for a final redirect.
                    // The hash will carry through to the final URL.
                    window.location.replace(url);
                }
            }
        }

    });

});
