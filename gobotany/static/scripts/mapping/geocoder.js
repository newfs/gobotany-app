/* Module for converting an address to geographic coordinates (geocoding):
 * wraps the Google Maps API geocoding service. 
 *
 * Note:
 * The map requires that this be set up at onload, not at jQuery ready. */

define([
    'mapping/google_maps'
], function (google_maps) {

    // Constructor
    function Geocoder() {
        this.geocoder = new google_maps.Geocoder();
    };

    Geocoder.prototype.geocode = function (address, response_callback,
                                           bounds /* optional */) {
        var request = {
            'address': address,
            'region': 'us'  // Return results biased to a particular region
        };
        if (bounds !== undefined) {
            // Return results biased to bounds, such as for a viewport.
            request['bounds'] = bounds
        }
        this.geocoder.geocode(request, response_callback);
    };

    // Call from your response callback function in order to help parse
    // the asynchronous response.
    Geocoder.prototype.handle_response = function (results, status) {
        var lat_lng = new google_maps.LatLng();
        if (status == google_maps.GeocoderStatus.OK) {
            lat_lng = results[0].geometry.location;
        }
        else {
            console.log('Geocode failed. Status: ' + status);
        }
        return lat_lng;
    };

    // Return the constructor function.
    return Geocoder;
});

