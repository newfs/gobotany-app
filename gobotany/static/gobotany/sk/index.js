dojo.provide('gobotany.sk.index');
dojo.require('dojo.cookie');

gobotany.sk.index.toggle_skip_getting_started = function(event) {
    var c = dojo.byId('skip_getting_started');
    dojo.cookie('skip_getting_started', c.checked ? 'skip' : '');
}

dojo.addOnLoad(function() {

    /* Build the last-plant URL from the saved cookie. */

    var last_plant_id_url = dojo.cookie('last_plant_id_url');
    if (last_plant_id_url) {
        var link_paragraph = dojo.query('#resume')[0];
        dojo.place('<a href="' + last_plant_id_url + '">' +
                   'Resume last plant identification</a>',
                   link_paragraph);
    }

    /* Set and unset the "Don't show" cookie each time the box is toggled. */

    dojo.connect(dojo.byId('skip_getting_started'), 'onclick', null, 
                 gobotany.sk.index.toggle_skip_getting_started);

});
