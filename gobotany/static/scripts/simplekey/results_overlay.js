require([
    'args',
    'jquery.tools.min',
    'simplekey/resources'
], function(args, ignore, resources) {

    var bv = resources.base_vector('simple', args.pile_slug);
    bv.done(function(base_vector) {
        $('.number-of-species .number').html(base_vector.length);
    });

    resources.pile_characters(args.pile_slug, []).done(function(clist) {
        $('.number-of-questions .number').html(clist.length);
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
