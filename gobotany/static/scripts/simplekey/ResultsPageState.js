/* ResultsPageState: for restoring and saving the state of the results
 * page user interface in order to support unique URLs and the ability
 * to "undo" actions using the Back button.
 */

define([
    'ember'
], function () {return Ember.Object.extend({

    init: function () {
        var hash = this.hash;

        this.set('hash', hash);
    },

    hash_has_filters: function () {
        return (this.hash.indexOf('_filters=') > -1);
    },

    filters_from_hash: function () {
        var filters = [];
        var filters_parameter;
        var i;
        var parameters = this.hash.split('&');

        for (i = 0; i < parameters.length; i += 1) {
            if (parameters[i].indexOf('_filters=') > -1) {
                filters_parameter = parameters[i];
                break;
            }
        }

        if (filters_parameter) {
            filters_parameter = filters_parameter.split('=')[1];
            filters = filters_parameter.split(',');
        }

        return filters;
    }

})});
