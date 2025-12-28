define([
    'bridge/jquery',
    'plantshare/sightings_locator_part',
    'plantshare/ask_the_botanist',
    'util/activate_image_gallery'
], function ($, SightingsLocatorPart, x1, x2) {

    $(window).load(function () {   // maps must be created at onload

        var sightings_locator_part =
            new SightingsLocatorPart('#sightings-locator');
        sightings_locator_part.setup();

        // Add keyboard support.
        let sightingsImageContainer = document.querySelector(
            "#recent-sightings-gallery .img-container");
        if (sightingsImageContainer) {
            sightingsImageContainer.addEventListener("keydown", function (event) {
                let key = event.key;
                // Only support the Enter key because the image in the
                // Recent Sightings gallery is a link to a sighting page,
                // i.e., not a button, where Space would also be needed.
                if (key === "Enter") {
                    event.preventDefault();
                    event.target.click();
                }
            });
        }
    });
});
