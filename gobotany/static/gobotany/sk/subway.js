// UI code for the Simple Key results/filter page.

dojo.provide('gobotany.sk.subway');

gobotany.sk.subway.click_more = function(event) {
    event.preventDefault();
    dojo.query('#subway ul ul').style('visibility', 'hidden');
    var this_ul = dojo.query(event.target.parentNode).query('ul');
    dojo.query(this_ul).style('visibility', 'visible');
}

gobotany.sk.subway.init = function() {
    dojo.query('#subway li a.more').connect(
        'onclick', gobotany.sk.subway.click_more);
}
