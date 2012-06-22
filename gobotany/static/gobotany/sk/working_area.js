define([
    'gobotany/sk/Choice',
    'gobotany/sk/Slider',
    'gobotany/sk/Length'
], function(Choice, Slider, Length) {

/*
 * Classes that create and maintain the working area.
 *
 * Upon instantiation, a working-area class draws the entire working area
 * for the filter that it has been given, and then un-hides the working
 * area.  Once up and running, it responds to three calls from outside
 * telling it that the outside world has changed.  It is also responsible
 * for handling every click and interaction inside the working area, and
 * for - when appropriate - forwarding the change in the filter state to
 * the outside world.
 *
 * Inputs:
 *
 * clear() - the user has pressed the "x" next to the filter's name in
 *     the sidebar summary, and the filter value should be moved back
 *     to "don't know" if that is not already the value.
 * dismiss() - the filter working area should be dismissed.
 *
 * Outputs:
 *
 * on_dismiss(filter) - called when the user dismisses the working area.
 */

/**
 * Return the correct working area class for a given filter.
 *
 * @param {Filter} filter The filter for which you want a working area.
 * @return {Class} The class that will manage this kind of working area.
 */
var working_area = {};
working_area.select_working_area = function(filter) {
    if (filter.value_type == 'TEXT')
        return Choice;
    else if (filter.is_length)
        return Length;
    else
        return Slider;
};

return working_area;

});
