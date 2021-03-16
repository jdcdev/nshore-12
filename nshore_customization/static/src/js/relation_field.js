odoo.define('nshore_customization.relation_field', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var relational_fields = require('web.relational_fields');
var _t = core._t;
var ControlPanel = require('web.ControlPanel');
var Pager = require('web.Pager');
relational_fields.FieldOne2Many.include({
    /**
     * We want to use our custom _renderControlPanel for the list.
     *
     * @override
     */
    _renderControlPanel: function () {
        if (!this.view) {
            return $.when();
        }
        var self = this;
        var defs = [];
        this.control_panel = new ControlPanel(this, "X2ManyControlPanel");
        this.pager = new Pager(this, this.value.count, this.value.offset + 1, 200, {
            single_page_hidden: true,
            withAccessKey: false,
            validate: function () {
                var isList = self.view.arch.tag === 'tree';
                // TODO: we should have some common method in the basic renderer...
                return isList ? self.renderer.unselectRow() : $.when();
            },
        });
        this.pager.on('pager_changed', this, function (new_state) {
            self.trigger_up('load', {
                id: self.value.id,
                limit: new_state.limit,
                offset: new_state.current_min - 1,
                on_success: function (value) {
                    self.value = value;
                    self._render();
                },
            });
        });
        this._renderButtons();
        defs.push(this.pager.appendTo($('<div>'))); // start the pager
        defs.push(this.control_panel.prependTo(this.$el));
        return $.when.apply($, defs).then(function () {
            self.control_panel.update({
                cp_content: {
                    $buttons: self.$buttons,
                    $pager: self.pager.$el,
                }
            });
        });
    },
});
})