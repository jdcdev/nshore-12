odoo.define('nshore_customization.send_print', function (require) {
"use strict";

/**
 * The List Controller controls the list renderer and the list model.  Its role
 * is to allow these two components to communicate properly, and also, to render
 * and bind all extra buttons/pager in the control panel.
 */

var core = require('web.core');
var BasicController = require('web.BasicController');
var DataExport = require('web.DataExport');
var pyeval = require('web.pyeval');
var Sidebar = require('web.Sidebar');

var _t = core._t;
var qweb = core.qweb;

odoo.nshore_customization = function(instance) {

var QWeb = openerp.web.qweb;
    _t = instance.web._t;

instance.web.FormView.include({
    load_form: function(data) {
        console.log("-----------------this ", this);
        var self = this;
        this.$el.find('.oe_send_print_so').click(this.on_button_send_print);
        return self._super(data);
    },
    on_button_send_print: function() {
//        this.dataset.index = null;
//        this.do_show();
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'mail.compose.message',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {'default_no_auto_thread': False,
                      'active_model': 'mail.message',
                      'default_subject':message.subject,
                      'default_body':message.body}
        });
        console.log('This============== ', this);
        console.log('Save & Close button method call...');
    },
});
};