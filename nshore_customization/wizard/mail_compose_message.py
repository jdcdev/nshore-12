# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail_and_print(self):
        self.send_mail_action()
        context = self.env.context.copy()
        active_id = context.get('active_ids', False) or \
                    context.get('default_res_id', False)
        active_model = context.get('default_model', False) or \
                       context.get('active_model', False)
        object = self.env[active_model].browse(active_id)
        return object.print_quotation()
