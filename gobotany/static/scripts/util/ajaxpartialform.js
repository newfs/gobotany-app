define([
    'bridge/jquery',
    'bridge/jquery.form'
], function(jquery, jqueryForm) {

    // AJAX partial forms
    // Allows a form that is partially editable and submitted via ajax.
    // The concept is that each field in the form will be given additional
    // data attributes to retain intial values.  Controls can appear for each
    // field which allow the field to be saved, or for that field to be reset
    // to the initial value.
    (function($) {

        var methods  = {
            init: function(options) {
                var $context = this;
                var settings = $.extend({
                    'autosaveTimeout': 0,
                    'onFieldReset': function() {},
                    'onSave': function(jsonParam) {}
                }, options);

                return this.each(function() {
                    var $form = $(this);

                    // Store the old value when the field gets focus
                    $form.find('input,select,textarea').bind('focus.ajaxpartialform', function() {
                        var $input = $(this);
                        $input.data('previousValue', $input.val());
                    });

                    // Restore the old value when "cancel" links or buttons are clicked
                    $form.find('.field-reset').bind('click.ajaxpartialform', function() {
                        var $input = $('.field-controls').has(this)
                                .siblings('.ajax-field')
                                .children('input,select,textarea')
                                .first();
                        var previous = $input.data('previousValue');
                        if(previous) {
                            $input.val(previous);
                        }

                        options.onFieldReset.call($input);
                    });

                    // Submit the form if any of the fields are saved.
                    $form.find('.field-save').bind('click.ajaxpartialform', function() {
                        $form.ajaxSubmit(function(json) {
                            if(json.success) {
                                $form.find('.ajax-field').each(function() {
                                    var $input = $(this)
                                            .children('input,select,textarea')
                                            .first();
                                    $input.data('previousValue', $input.val());
                                });
                            }

                            options.onSave.call($form, json);
                        });

                    });

                });
            }
        };

        $.fn.ajaxpartialform = function(method) {
            if ( methods[method] ) {
              return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
            } else if ( typeof method === 'object' || ! method ) {
              return methods.init.apply( this, arguments );
            } else {
              $.error( 'Method ' +  method + ' does not exist on jQuery.ajaxpartialform' );
            }
        };
     })(jquery);

});
