# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InvoiceList(models.Model):
    _name = 'invoice.list'

    def get_invoice(self):
        """Remove prduct name in description sale."""
        context = dict(self._context or {})
        invoices = self.env['account.invoice'].browse(context['active_ids'])
        for invoice in invoices:
            for res in invoice.invoice_line_ids:
                if res.invoice_id.type in ('out_invoice', 'out_refund'):
                    taxes = res.product_id.taxes_id.filtered(lambda r: r.company_id == res.company_id) or res.account_id.tax_ids or res.invoice_id.company_id.account_sale_tax_id
                else:
                    taxes = res.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == res.company_id) or res.account_id.tax_ids or res.invoice_id.company_id.account_purchase_tax_id
                if res.invoice_id.fiscal_position_id:
                    pass
                res.invoice_line_tax_ids = res.invoice_id.fiscal_position_id.map_tax(taxes, res.product_id, res.invoice_id.partner_id)
            invoice._onchange_invoice_line_ids()
            invoice._compute_amount()
            invoice._onchange_partner_id()

    def validate_invoice(self):
        """Remove prduct name in description sale."""
        context = dict(self._context or {})
        invoices = self.env['account.invoice'].browse(context['active_ids'])
        for invoice in invoices:
            invoice.action_invoice_open()
