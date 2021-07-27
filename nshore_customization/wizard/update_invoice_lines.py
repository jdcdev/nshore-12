# -*- coding: utf-8 -*-

from odoo import models, api


class UpdateInvoiceLines(models.TransientModel):
    """Added new module import Inventory adjustment."""

    _name = 'update.account.invoice'
    _description = "Update Invoice Line's Price field."

    @api.multi
    def update_invoice_lines(self):
        """Update Invoice Lines with products prices."""
        active_ids = self.env.context.get('active_ids')
        invoice_list = self.env['account.invoice'].browse(active_ids)
        for inv in invoice_list:
            for inv_lines in inv.invoice_line_ids:
                inv_lines.update({
                    'product_net_cost': inv_lines.product_id.net_cost,
                    'product_list_price': inv_lines.product_id.lst_price,
                })
