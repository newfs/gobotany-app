dojo.provide('gobotany.sk.rulertest');
dojo.require('gobotany.sk.RulerSlider');

dojo.declare('gobotany.sk.rulertest', null, {

    constructor: function() {
        var updater = function() {};
        dojo.query('#filter-working').style({display: 'block'});

        this.count = 0;
        this.working = dojo.byId('filter-working');
        var RS = gobotany.sk.RulerSlider;

        new RS(this.n(), this.nextid(), 600, 0.0, 6.31, 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 10, 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 15.8, 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 25.1, 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 39.8, 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 63.1, 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 100, 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 158., 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 251., 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 398., 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 631., 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 1000, 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 1580., 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 2510., 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 3980., 1.0, updater);
        new RS(this.n(), this.nextid(), 600, 0.0, 6310., 1.0, updater);
    },

    n: function() {
        return dojo.create('div', null, this.working);
    },

    nextid: function() {
        this.count += 1;
        return 'character_slider' + this.count;
    }
});
