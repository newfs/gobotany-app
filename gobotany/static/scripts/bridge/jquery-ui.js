// AMD wrapper for jquery-ui library.
// This should ensure the AMD loader properly caches jquery
// and only loads it once, and we can be sure that this library
// has jquery loaded before it attempts to load. This also serves
// as a thin abstraction layer so we don't have to worry about
// versioned filenames in our module references.
//
// This is a custom build of jQuery UI from http://jqueryui.com/download/.
// Start by deselecting everything there, then add the items you need.
// The only items included in our build are:
// - from the UI Core category: Core, Widget
// - from the Effects category: Effects Core
//
// Known dependencies for components we use:
// For smoothDivScroll: Core, Widget, Effects Core
// For any other components: ? (add here eventually)
//
// Once you have downloaded a new custom build of jQuery UI and updated
// the line below to reference the new version, please also edit the new
// jQuery UI JS file to add an AMD wrapper as seen in the old version
// that you are replacing.
define([
    'lib/jquery-ui-1.9.2.custom.min'
], function() {});
