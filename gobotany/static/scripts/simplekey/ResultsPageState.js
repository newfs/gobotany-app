/* ResultsPageState: for restoring and saving the state of the results
 * page user interface in order to support unique URLs and the ability
 * to "undo" actions using the Back button.
 */

define([
    'ember'
], function() {return Ember.Object.extend({

    init: function() {
        var hash = this.hash;

        this.set('hash', hash);
    }

})});
