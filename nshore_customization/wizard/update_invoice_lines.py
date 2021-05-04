# -*- coding: utf-8 -*-

from odoo import models, api


class UpdateInvoiceLines(models.TransientModel):
    """Added new module import Inventory adjustment."""

    _name = 'update.account.invoice'

    @api.multi
    def update_invoice_lines(self):
        """Update Invoice Lines with products prices."""
        active_ids = self.env.context.get('active_ids')
        invoice_list = self.env['account.invoice'].browse(active_ids)
        for inv in invoice_list:
            print("\n\n\n inv", inv)
            for inv_lines in inv.invoice_line_ids:
                print("inv_lines", inv_lines)
                inv_lines.update({
                    'product_net_cost': inv_lines.product_id.net_cost,
                    'product_list_price': inv_lines.product_id.lst_price,
                })
