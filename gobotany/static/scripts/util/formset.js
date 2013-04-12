define([
    'bridge/jquery', 
], function ($) {

    var configuration = {
        'formSelector': '',
        'formTemplateSelector': '',
        'addLinkSelector': '',
        'removeLinkSelector': ''
    };

    var $formContainer = null;

    var formset = {

        init: function(new_config) {
            configuration = $.extend({}, configuration, new_config);
            $formContainer = $(configuration.formSelector).parent();
            var that = this;
            if('' != configuration.addLinkSelector) {
                $(configuration.addLinkSelector).click(function(e) {
                    e.preventDefault();
                    that.add_form()
                });
            }
            if('' != configuration.removeLinkSelector) {
                $(configuration.removeLinkSelector).live('click', function(e) {
                    e.preventDefault();
                    that.remove_form(this);
                });
            }
        },

        add_form: function() {
            var form_idx = $('#id_form-TOTAL_FORMS').val();
            $formContainer.append(
                $(configuration.formTemplateSelector).clone()
                    .wrap('<p>').parent().html()
                    .replace(/__prefix__/g, form_idx)
            );
            $('#id_form-TOTAL_FORMS').val(parseInt(form_idx) + 1);
        },

        remove_form: function(clicked) {
            var form_idx = $('#id_form-TOTAL_FORMS').val();
            $removed = $(clicked).parents(configuration.formSelector);
            console.log('Removing node');
            $removed.remove();
            $('#id_form-TOTAL_FORMS').val(parseInt(form_idx) - 1);
        }
    
    };

    return formset;

});

