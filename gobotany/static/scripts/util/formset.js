define([
    'bridge/jquery', 
], function ($) {

    var configuration = {
        'formSelector': '',
        'formTemplateSelector': '',
        'addLinkSelector': '',
        'removeLinkSelector': '',
        'canDelete': false
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

                    if(configuration.canDelete && that.is_existing(this)) {
                        that.delete_form(this);
                    } else {
                        that.remove_form(this);
                    }
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
            $removed.remove();
            $('#id_form-TOTAL_FORMS').val(parseInt(form_idx) - 1);
        },

        delete_form: function(clicked) {
            $deleted = $(clicked).parents(configuration.formSelector);
            var $delete_box = $deleted.find('div.form-data input[type="checkbox"]');
            // Find the delete box in this form and check it.
            $delete_box.each(function(index) {
                $this = $(this);
                if (-1 != $this.attr('name').search(/form-\d+-DELETE/)) {
                    console.log('Delete checkbox found.');
                    $this.attr('checked', 'checked');
                }
            });
            // Hide the form, but don't decrement the number of forms,
            // since we still need to submit the deleted one.
            $deleted.hide();
        },

        is_existing: function(clicked) {
            console.log('is_existing called.');
            var $clicked_form = $(clicked).parents(configuration.formSelector);
            var $id_box = $clicked_form.find('div.form-data input[type="hidden"]');
            var is_existing = false;
            $id_box.each(function(index) {
                $this = $(this);
                if ($this.val() && 
                        -1 != $this.attr('name').search(/form-\d+-id/)) {
                    console.log('Found id value.  Pre-existing form.');
                    is_existing = true;
                    return false;
                }
            });

            return is_existing;
        }
    
    };

    return formset;

});

