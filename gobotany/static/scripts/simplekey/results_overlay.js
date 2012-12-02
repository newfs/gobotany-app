define([
    'bridge/jquery',
    'bridge/underscore',
    'simplekey/resources',
    'util/document_is_ready'
], function($, _, resources, document_is_ready) {

    var results_overlay_init = function(
        pile_slug, key_vector_ready, pile_taxa_ready
    ) {
        $.when(
            document_is_ready,
            key_vector_ready,
            pile_taxa_ready
        ).done(function(x, key_vector, pile_taxa_vector) {
            var k = key_vector[0].species;
            var j = _.intersection(k, pile_taxa_vector);
            $('.number-of-species .number').html(j.length);
        });

        $.when(
            document_is_ready,
            resources.pile_characters(pile_slug)
        ).done(function(x, clist) {
            $('.number-of-questions .number').html(clist.length);
        });

        document_is_ready.done(function() {if (!original_location_hash) {

            $('#intro-overlay').overlay({
                mask: {
                    color: $('body').css('background-color'),
                    loadSpeed: 500,
                    opacity: 0.5,
                    top: 0
                },
                closeOnClick: true,
                load: true
            }).click(function(event) {
                $('#intro-overlay').data('overlay').close();
            });

            /* The jQuery Tools Overlay "mask" is actually a jQuery Tools
             * Expose widget.  For some reason, Expose gives its mask a
             * style of "position: absolute" which means that once the plant
             * images are loaded and the page height has increased, the user
             * can scroll down past the mask.  Therefore we change its
             * position to "fixed" so that it stays in the viewport.
             */
            $('#exposeMask').css('position', 'fixed');

        }});
    };

    return results_overlay_init;
});
