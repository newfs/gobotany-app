require([
    'jquery.tools.min'
], function() {
    $(document).ready(function() {
        $('#intro-overlay-off').overlay({
            mask: {
                color: '#f0f0f0',
                loadSpeed: 200,
                opacity: 0.9
            },
            closeOnClick: true,
            load: true
        });
    });
});
