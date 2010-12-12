// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, gobotany */

dojo.provide('gobotany.sk.partners');

gobotany.sk.partners.partner_site = function() {
    // This is less than ideal, because there is a separate place on the
    // server side for the same knowledge, but perhaps this file could
    // be generated dynamically on the server side instead.

    var partner_site = null;

    if (window.location.host.indexOf(':8001') > -1) {
        partner_site = 'montshire';
    }

    return partner_site;
};
