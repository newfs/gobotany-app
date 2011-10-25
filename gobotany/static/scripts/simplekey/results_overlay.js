require([
    'args',
    'jquery.tools.min',
    'simplekey/resources'
], function(args, ignore, resources) {

    var d = resources.species_vector('simple', args.pile_slug);
    d.done(function(species_vector) {
        $('.number-of-species .number').html(species_vector.length);
    });

    $(document).ready(function() {

        $('#intro-overlay').overlay({
            mask: {
                color: $('body').css('background-color'),
                loadSpeed: 500,
                opacity: 0.8,
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
        console.log($('#exposeMask').css('position', 'fixed'));
    });
});
