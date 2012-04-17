define([
    'ember-metal',
    'ember-runtime',
    'underscore-min'
], function() {

    return Ember.Object.create({
        testval: _.intersect([1, 2, 3], [2, 3, 4])
    });

});
