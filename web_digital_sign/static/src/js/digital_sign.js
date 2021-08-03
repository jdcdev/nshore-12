odoo.define('web_digital_sign.web_digital_sign', function (require) {
    "use strict";

    var core = require('web.core');
    var BasicFields= require('web.basic_fields');
    var FormController = require('web.FormController');
    var Registry = require('web.field_registry');
    var utils = require('web.utils');
    var session = require('web.session');
    var field_utils = require('web.field_utils');
    var Dialog = require('web.Dialog');
    var FormController = require('web.FormController');
    var _t = core._t;
    var QWeb = core.qweb;
    window.not_signed = '';

    FormController.include({
        _onSave: function (ev) {
            ev.stopPropagation(); // Prevent x2m lines to be auto-saved
            var self = this;
            var context = self.initialState.context.form_sign
            if (context){
                var signature = this.$(".signature").jSignature("getData", 'image');
                this.is_empty_sign = signature ? window.not_signed[1] === signature[1] : true;
                if (this.is_empty_sign){
                    alert(_t(
                        'Please Sign this Invoice First'
                    ));
                }
                else{
                    self._disableButtons();
                    self.saveRecord().always(function () {
                        self._enableButtons();
                        var last_link = $('.breadcrumb .o_back_button a')
                        if (last_link.length)
                        {
                            last_link.trigger('click');
                        }
                        else
                        {
                            this.do_action({
                                type: 'ir.actions.act_window',
                                res_model: 'account.invoice',
                                res_id: self.initialState.context.id,
                                views: [[self.initialState.context.view_id, 'form']],
                                target: 'current',
                            });
                        }
                    });
                }
            }
            else{
                self._disableButtons();
                self.saveRecord().always(function () {
                    self._enableButtons();
                });
            }

        },
    });

    var FieldSignature = BasicFields.FieldBinaryImage.extend({
        template: 'FieldSignature',
        events: _.extend({}, BasicFields.FieldBinaryImage.prototype.events, {
            'click .save_sign': '_on_save_sign',
            'click #sign_clean': '_on_clear_sign',
            /*'change .signature': '_on_change_sign',*/

        }),
        jsLibs: ['/web_digital_sign/static/lib/jSignature/jSignatureCustom.js'],
        placeholder: "/web/static/src/img/placeholder.png",
        init: function (parent, name, record) {
            this._super.apply(this, arguments);
            this.sign_options = {
                'decor-color': '#D1D0CE',
                'color': '#000',
                'background-color': '#fff',
                'height': '550',
                'width': '850',
            };
            this.empty_sign = [];
        },
        start: function () {
            var self = this;
            this.$(".signature").jSignature("init", this.sign_options);
            this.$(".signature").attr({
                "tabindex": "0",
                'height': "100",
            });
            this.empty_sign = this.$(".signature").jSignature("getData",
                'image');
            window.not_signed = this.empty_sign
            self._render();
            
        },
        _on_clear_sign: function () {
            this.$(".signature > canvas").remove();
            this.$('> img').remove();
            this.$(".signature").attr("tabindex", "0");
            var sign_options = {
                'decor-color': '#D1D0CE',
                'color': '#000',
                'background-color': '#fff',
                'height': '550',
                'width': '850',
                'clear': true,
            };
            this.$(".signature").jSignature(sign_options);
            /*this.$(".signature").focus();*/
            this._setValue(false);
        },
        _on_save_sign: function (value_) {
            var self = this;
            this.$('> img').remove();
            var signature = this.$(".signature").jSignature("getData", 'image');
            var is_empty = signature;
            self.empty_sign[1] === signature[1];
            false;
            if (is_empty.length > 0 && typeof signature !== "undefined" && signature[1]) {
                self._setValue(signature[1]);
            }
        },

        _render: function () {
            var self = this;
            var url = this.placeholder;
            if (this.value && !utils.is_bin_size(this.value)) {
                url = 'data:image/png;base64,' + this.value;
            } else if (this.value) {
                url = session.url('/web/image', {
                    model: this.model,
                    id: JSON.stringify(this.res_id),
                    field: this.nodeOptions.preview_image || this.name,
                    unique:
                    field_utils.format.datetime(
                        this.recordData.__last_update).replace(/[^0-9]/g, ''),
                });
            } else {
                url = this.placeholder;
            }
            if (this.mode === "readonly") {
                var $img = $(QWeb.render("FieldBinaryImage-img", {
                    widget: self,
                    url: url,
                }));
                this.$('> img').remove();
                this.$(".signature").hide();
                this.$el.prepend($img);
                $img.on('error', function () {
                    self.on_clear();
                    $img.attr('src', self.placeholder);
                    self.do_warn(_t("Image"),
                        _t("Could not display the selected image."));
                });
            } else if (this.mode === "edit") {
                this.$('> img').remove();
                if (this.value) {
                    var field_name = this.name;
                    this.nodeOptions.preview_image;
                    this.name;
                    var context = 'cont'
                    self._rpc({
                        model: this.model,
                        method: 'read',
                        args: [this.res_id, [field_name], context=context],
                    }).done( function (data) {
                        if (data) {
                            var field_desc =
                            _.values(_.pick(data[0], field_name));
                            self.$(".signature").jSignature("clear");
                            self.$(".signature").jSignature("setData",
                                'data:image/png;base64,' + field_desc[0]);
                        }
                    });
                } else {
                    this.$('> img').remove();
                    this.$('.signature > canvas').remove();
                    var sign_options = {
                        'decor-color': '#D1D0CE',
                        'color': '#000',
                        'background-color': '#fff',
                        'height': '550',
                        'width': '850',
                    };
                    this.$(".signature").jSignature("init", sign_options);
                }
            } else if (this.mode === 'create') {
                this.$('> img').remove();
                this.$('> canvas').remove();
                if (!this.value) {
                    this.$(".signature").empty().jSignature("init", {
                        'decor-color': '#D1D0CE',
                        'color': '#000',
                        'background-color': '#fff',
                        'height': '550',
                        'width': '850',
                    });
                }
            }
        },
    });

    FormController.include({
        saveRecord: function () {
            this.$('.save_sign').click();
            return this._super.apply(this, arguments);
        },
    });

    Registry.add('signature', FieldSignature);


});
