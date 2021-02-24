odoo.define('nshore_customization.data_export_inherit', function (require) {
"use strict";

var core = require('web.core');
var DataExports = require('web.DataExport');
var QWeb = core.qweb;
var _t = core._t;
DataExports.include({
    /*Added Search Input into Export Event*/
    events: _.extend({}, DataExports.prototype.events, {
        'input .o_export_search_input': '_onSearchInput'
    }),
    /*Search function to search fields in export dialogue */
    _onSearchInput: function (ev) {
    var searchText = $(ev.currentTarget).val().trim().toUpperCase();
        if (!searchText) {
            this.$('.o_no_match').remove();
            this.$(".o_export_tree_item").show();
            this.$(".o_export_tree_item.haschild:not(.show) .o_export_tree_item").hide();
            return;
        }

        var matchItems = this.$(".o_tree_column").filter(function () {
            var title = this.getAttribute('title');
            return this.innerText.toUpperCase().indexOf(searchText) >= 0
                || title && title.toUpperCase().indexOf(searchText) >= 0;
        }).parent();
        this.$(".o_export_tree_item").hide();
        if (matchItems.length) {
            this.$('.o_no_match').remove();
            _.each(matchItems, function (col) {
                var $col = $(col);
                $col.show();
                $col.parents('.haschild.show').show();
                if (!$col.parent().hasClass('show') && !$col.parent().hasClass('o_field_tree_structure')) {
                    $col.hide();
                }
            });
        } else if (!this.$('.o_no_match').length) {
            this.$(".o_field_tree_structure").append($("<h3/>", {
                class: 'text-center text-muted mt-5 o_no_match',
                text: _t("No match found.")
            }));
        }
    },
});
});