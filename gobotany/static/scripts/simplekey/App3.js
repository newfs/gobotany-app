define([
    'ember'
], function(Ember) {
    // Global assignment makes "App3" available to handlebar templates.
    console.log('doing app3');
    App3 = Ember.Application.create();
    return App3;
});
