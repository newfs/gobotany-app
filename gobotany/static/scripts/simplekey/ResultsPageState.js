/* ResultsPageState: for restoring and saving the state of the results
 * page user interface in order to support unique URLs and the ability
 * to "undo" actions using the Back button.
 */

define([
    'ember'
], function () {return Ember.Object.extend({

    init: function (args) {
        var hash = this.hash || '',
            filter_names = this.filter_names || [],
            filter_values = this.filter_values || [],
            photo_type = this.photo_type || '',
            tab_view = this.tab_view || '';
            
        delete this.hash;
        delete this.filter_names;
        delete this.filter_values;
        delete this.photo_type;
        delete this.tab_view;

        if (hash[0] === '#') {
            hash = hash.substr(1);
        }
        this.set('_hash', hash);

        this.set('_filter_names', filter_names);
        this.set('_filter_values', filter_values);
        this.set('_photo_type', photo_type);
        this.set('_tab_view', tab_view);
    },

    hash_has_filters: function () {
        return (this._hash.indexOf('_filters=') > -1);
    },

    filter_names: function () {
        var filter_names = [],
            filters_parameter,
            i,
            parameters = this._hash.split('&');

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
        var decoded_hash = decodeURIComponent(this._hash),
            filter_values = {},
            i,
            parameters = decoded_hash.split('&'),
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

    _parameter_from_hash: function (parameter_name) {
        var i,
            parameter_key,
            parameter_value,
            parameters = this._hash.split('&');

        parameter_key = '_' + parameter_name;
        for (i = 0; i < parameters.length; i += 1) {
            if (parameters[i].indexOf(parameter_key) > -1) {
                parameter_value = parameters[i].split('=')[1];
                break;
            }
        }

        return parameter_value;
    },

    tab_view: function () {
        return this._parameter_from_hash('view');
    },

    photo_type: function () {
        return this._parameter_from_hash('show');
    },

    hash: function (args) {
        var hash = '#_filters=',
            i,
            key;

        for (i = 0; i < this._filter_names.length; i += 1) {
            if (i > 0) {
                 hash += ',';
            }
            hash += this._filter_names[i];
        }

        for (key in this._filter_values) {
            if (this._filter_values.hasOwnProperty(key)) {    
                hash += '&' + key + '=' +
                    encodeURIComponent(this._filter_values[key]);
            }
        }

        hash += '&_view=' + this._tab_view;
        hash += '&_show=' + this._photo_type;

        return hash;
    }

})});
