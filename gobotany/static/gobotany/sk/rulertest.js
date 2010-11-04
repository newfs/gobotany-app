dojo.provide('gobotany.sk.rulertest');
dojo.require('gobotany.sk.RulerSlider');

dojo.declare('gobotany.sk.rulertest', null, {

    constructor: function() {
        var updater = function() {};
        dojo.query('#filter-working').style({display: 'block'});

        this.working = dojo.byId('filter-working');

        new gobotany.sk.RulerSlider(this.n(), 0.0, 1, 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 2.15, 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 4.64, 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 10.0, 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 21.5, 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 46.4, 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 100.0, 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 215., 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 464., 1.0, updater);
        new gobotany.sk.RulerSlider(this.n(), 0.0, 1000.0, 1.0, updater);
    },

    n: function() {
        return dojo.create('div', null, this.working);
    }
});
