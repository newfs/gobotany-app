define([
    'ember-metal',
    'ember-runtime',
    'jquery',
    'underscore-min'
], function(x, x, $, x) {

    return Ember.Object.create({

        testval: 1,

        add_filter: function(short_name, filter_getter) {
            var d = $.Deferred();
            var self = this;
            filter_getter(short_name).done(function() {
                self.testval = 2;
                d.resolve(self);
            });
            return d;
        }
    });

});
