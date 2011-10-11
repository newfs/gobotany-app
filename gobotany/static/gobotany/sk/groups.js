/*
 * Code for adding behavior to the plant groups and subgroups pages.
 */

dojo.provide('gobotany.sk.groups');

dojo.require('gobotany.sk.glossary');

dojo.declare('gobotany.sk.groups.GroupsHelper', null, {

    constructor: function() {
        this.glossarizer = gobotany.sk.glossary.Glossarizer();
    },

    setup: function() {
        var that = this;
        dojo.query('.key-char, .exceptions').forEach(function(node) {
            that.glossarizer.markup(node);
        });
    }
});
