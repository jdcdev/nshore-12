odoo.define('nshore_customization.favorites_menu_inherit', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var fav_menu = require('web.FavoriteMenu');
var _t = core._t;
fav_menu.include({
     start: function () {
        var self = this;
        this.$filters = {};
        this.$save_search = this.$('.o_save_search');
        this.$save_name = this.$('.o_save_name');
        this.$inputs = this.$save_name.find('input');
        this.$user_divider = this.$('.dropdown-divider.user_filter');
        this.$shared_divider = this.$('.dropdown-divider.shared_filter');
        this.$inputs.eq(0).val(this.searchview.get_title());
        var $shared_filter = this.$inputs.eq(1),
            $default_filter = this.$inputs.eq(2);
        var default_boolean = true
        this._rpc({
                model: 'res.company',
                method: 'get_company_default_boolean',
                args: [],
            }).then(function (result) {
                if (result == false){
                    $shared_filter.click(function () {$default_filter.prop('checked', false);});
                    $default_filter.click(function () {$shared_filter.prop('checked', false);});
                }
                else{
                    $shared_filter.click(function () {$default_filter.prop('checked', false);});
                    $default_filter.click(function () {$shared_filter.prop('checked', true);});
                }
            });

        return this._super();
    }, 
});
})
