// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, console, gobotany, global_toggleQuestions */
//
// JSLint option settings:
/*jslint sloppy: true, vars: true, white: true, nomen: true, maxerr: 50,
  indent: 4 */

dojo.provide('gobotany.sk.GettingStartedHelper');

dojo.require('dojo.cookie');

dojo.declare('gobotany.sk.GettingStartedHelper', null, {
    constants: {SKIP_PAGE_COOKIE_NAME: 'skip_help_start'},
    checkbox: null,

    constructor: function() {
        this.checkbox = dojo.query('#skip-page')[0];
        if (this.checkbox === undefined) {
            console.error('GettingStartedHelper.js: Check box not found.');
        }
    },

    _set_skip_page_checkbox: function(checkbox) {
        var cookie_value = dojo.cookie(this.constants.SKIP_PAGE_COOKIE_NAME);
        checkbox.checked = (cookie_value === 'y');
    },

    _set_skip_page_cookie: function() {
        var DAYS_UNTIL_COOKIE_EXPIRES = 10000;
        var cookie_value = 'n';
        if (this.checkbox.checked) {
            cookie_value = 'y';
        }
        dojo.cookie(this.constants.SKIP_PAGE_COOKIE_NAME, cookie_value,
            {path: '/', expires: DAYS_UNTIL_COOKIE_EXPIRES});
    },

    _set_up_skip_checkbox: function() {
        // Set up the checkbox that allows skipping this Getting Started
        // help page when starting a new plant identification session.

        // Wire up a checkbox handler that changes the cookie value.
        dojo.connect(this.checkbox, 'onchange', this,
            this._set_skip_page_cookie);

        // Set the checkbox state from the current cookie value.
        this._set_skip_page_checkbox(this.checkbox);
    },

    setup: function() {
        this._set_up_skip_checkbox();
    }
});
