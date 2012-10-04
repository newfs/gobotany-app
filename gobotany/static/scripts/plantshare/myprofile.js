define([
    'bridge/jquery', 
    'bridge/jquery.form'
], function($, jqueryForm) {

    $(document).ready(function() {
        $('.edit-link').click(function(eventObj) {
            // Hide any existing form inputs
            $('div.edit').hide();
            $('div.display').show();

            var link = eventObj.target;
            var display_field = $('div.display').has(link);
            var edit_field = display_field.siblings('div.edit');
            display_field.hide();
            edit_field.show();

            return false;
        });
    });

});
