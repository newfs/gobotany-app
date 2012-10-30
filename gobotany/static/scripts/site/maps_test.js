define([
    'bridge/jquery',
    'mapping/google_maps',
    'mapping/sightings_map'
], function ($, google_maps, SightingsMap) {

    $(document).ready(function () {
        $('div.map[data-type="sightings"]').each(function () {
            var sightings_map = new SightingsMap(this);
            sightings_map.setup();
            sightings_map.mark_center();
        });
    });
});

