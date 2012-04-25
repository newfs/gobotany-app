/* ResultsPageState: for restoring and saving the state of the results
 * page user interface in order to support unique URLs and the ability
 * to "undo" actions using the Back button.
 */

define([
    'ember'
], function () {return Ember.Object.extend({

    init: function () {
        var hash = this.hash;

        if (hash[0] === '#') {
            hash = hash.substr(1);
        }

        this.set('hash', hash);
    },

    hash_has_filters: function () {
        return (this.hash.indexOf('_filters=') > -1);
    },

    filter_names: function () {
        var filter_names = [],
            filters_parameter,
            i,
            parameters = this.hash.split('&');

        for (i = 0; i < parameters.length; i += 1) {
            if (parameters[i].indexOf('_filters=') > -1) {
                filters_parameter = parameters[i];
                break;
            }
        }

        if (filters_parameter) {
            filters_parameter = filters_parameter.split('=')[1];
            filter_names = filters_parameter.split(',');
        }

        return filter_names;
    },

    filter_values: function () {
        var filter_values = {},
            i,
            parameters = this.hash.split('&'),
            parts;

        for (i = 0; i < parameters.length; i += 1) {
            parts = parameters[i].split('=');
            // Parameters without leading underscores represent filters
            // that have a value selected.
            if (parts[0][0] !== '_') {
                filter_values[parts[0]] = parts[1];
            }
        }

        return filter_values;
    },

    parameter_from_hash: function (parameter_name) {
        var i,
            parameter_key,
            parameter_value,
            parameters = this.hash.split('&');

        parameter_key = '_' + parameter_name;
        for (i = 0; i < parameters.length; i += 1) {
            if (parameters[i].indexOf(parameter_key) > -1) {
                parameter_value = parameters[i].split('=')[1];
                break;
            }
        }

        return parameter_value;
    },

})});
