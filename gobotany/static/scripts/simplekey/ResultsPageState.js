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

    filters_from_hash: function () {
        var filters = [],
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
            filters = filters_parameter.split(',');
        }

        return filters;
    },

    filter_values_from_hash: function () {
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

    visible_filter_from_hash: function () {
        var i,
            parameters = this.hash.split('&'),
            visible_filter;

        for (i = 0; i < parameters.length; i += 1) {
            if (parameters[i].indexOf('_visible=') > -1) {
                visible_filter = parameters[i].split('=')[1];
                break;
            }
        }

        return visible_filter;
    },

    tab_view_from_hash: function () {
        var i,
            parameters = this.hash.split('&'),
            tab_view;

        for (i = 0; i < parameters.length; i += 1) {
            if (parameters[i].indexOf('_view=') > -1) {
                tab_view = parameters[i].split('=')[1];
                break;
            }
        }

        return tab_view;
    },



})});
