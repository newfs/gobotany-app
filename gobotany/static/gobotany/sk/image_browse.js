dojo.provide('gobotany.sk.image_browse');

// Common code used for browsing images on the plant preview popup and 
// the species page.

gobotany.sk.image_browse.set_up_navigation_links = function(taxon_images,
    image_area_css_selector, change_image_function) {

    // Wire up the previous and next links, or hide them if not needed.

    var links = dojo.query(image_area_css_selector + ' a');
    for (var i = 0; i < links.length; i++) {
        if (taxon_images.length > 1) {
            dojo.removeClass(links[i], 'hidden');
            dojo.connect(links[i], 'onclick', change_image_function);
        }
        else {
            dojo.addClass(links[i], 'hidden');
        }
    }
};

gobotany.sk.image_browse.get_current_image_index = function(current_image_url,
    images_info, url_property_name) {

    // Figure out which image is currently showing. The URL property name
    // is for supporting URLs for different image sizes, i.e., full images or
    // thumbnails.

    var current_image_index = null;
    var i = 0;
    while (current_image_index === null && i < images_info.length) {
        if (current_image_url === images_info[i][url_property_name]) {
            current_image_index = i;
        }
        i++;
    }
    
    return current_image_index;
};

gobotany.sk.image_browse.get_next_image_index = function(
    image_area_css_selector, number_of_images, current_image_index) {

    // Figure out which image to show next.

    var images_area = dojo.query(image_area_css_selector)[0];
    var new_image_index = current_image_index;

    if (images_area.innerHTML.indexOf('next') >= 0) {
        new_image_index++;
    }
    else if (images_area.innerHTML.indexOf('prev') >= 0) {
        new_image_index--;
    }

    if (new_image_index < 0) {
        new_image_index = number_of_images - 1;
    }
    else if (new_image_index > number_of_images - 1) {
        new_image_index = 0;
    }
    
    return new_image_index;
};

gobotany.sk.image_browse.set_image = function(image_node, message_node,
    image_url, image_alt_text, index, num_images) {
    
    // Set the image URL and alt text, and set the count message.
    
    dojo.attr(image_node, 'src', image_url);
    dojo.attr(image_node, 'alt', image_alt_text);
    message_node.innerHTML = (index + 1) + ' of ' + num_images;
};
