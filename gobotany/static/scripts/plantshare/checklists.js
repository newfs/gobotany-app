define([
    'bridge/jquery', 
], function ($) {

    $('a.delete').click(function (e) {
        // Delete a single checklist.

        e.preventDefault();

        var $cells = $(this).parent().siblings();
        var $checkbox = $cells.first().find('input');
        // Check the (hidden) checkbox to mark for deletion.
        $checkbox.prop('checked', true);

        // POST the form to delete it.
        $('form').attr('action', $(this).attr('href'));
        $('form').submit();
    });

})
