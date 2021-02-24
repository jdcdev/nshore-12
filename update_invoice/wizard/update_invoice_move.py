# -*- coding: utf-8 -*-

from odoo import models


class InvoiceList(models.TransientModel):
    """Model create for create Journal Entries."""

    _name = 'update.invoice.move'
    _description = 'Update Invoice Moves'

    def update_invoice_move_partner(self):
        """Function call to update invoice,move partner."""
        account_invoice = self.env['account.invoice'].search([])
        for invoice in account_invoice:
            if invoice.partner_id.company_type == 'person':
                if invoice.move_id:
                    for move_lines in invoice.move_id.line_ids:
                        move_lines.update({
                            'partner_id': invoice.partner_id.parent_id.id})
                invoice.update({
                    'partner_id': invoice.partner_id.parent_id.id})
