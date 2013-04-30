define([
    'bridge/jquery', 
], function ($) {

   $('.delete-btn').click(function(e) {
       e.preventDefault();

       $('form').attr('action', $(this).attr('href'));
       $('form').submit();
   });

})
