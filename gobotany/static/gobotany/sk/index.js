dojo.provide('gobotany.sk.index');
dojo.require('dojo.cookie');

dojo.addOnLoad(function() {
    var last_plant_id_url = dojo.cookie('last_plant_id_url');
    if (last_plant_id_url) {
        var link_paragraph = dojo.query('#resume')[0];
        dojo.place('<a href="' + last_plant_id_url + '">' +
                   'Resume last plant identification</a>',
                   link_paragraph);
    }
});