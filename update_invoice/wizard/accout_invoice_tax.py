# -*- coding: utf-8 -*-

from odoo import models
from odoo.tools import float_compare

class InvoiceList(models.Model):
    _name = 'invoice.list'

    def calculate_taxes(self):
        """Remove prduct name in description sale."""
        context = dict(self._context or {})
        invoices = self.env['account.invoice'].browse(context['active_ids'])
        for invoice in invoices:
            invoice._onchange_partner_id()
            invoice._onchange_partner_shipping_id()
            for res in invoice.invoice_line_ids:
                res.uom_id = res.product_id.uom_id.id
                if res.invoice_id.type in ('out_invoice', 'out_refund'):
                    taxes = res.product_id.taxes_id.filtered(lambda r: r.company_id == res.company_id) or res.account_id.tax_ids or res.invoice_id.company_id.account_sale_tax_id
                else:
                    taxes = res.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == res.company_id) or res.account_id.tax_ids or res.invoice_id.company_id.account_purchase_tax_id
                if res.invoice_id.fiscal_position_id:
                    pass
                res.invoice_line_tax_ids = res.invoice_id.fiscal_position_id.map_tax(taxes, res.product_id, res.invoice_id.partner_id)
            invoice._onchange_invoice_line_ids()
            invoice._compute_amount()

    def fetch_saleperson(self):
        """ Assign External ID as Reference"""
        # invoices = self.env['account.invoice'].browse(context['active_ids'])
        invoices = self.env['account.invoice'].search([])
        for invoice in invoices:
            if invoice.partner_id and invoice.partner_id.user_id:
                invoice.user_id = invoice.partner_id.user_id

    def generate_reference(self):
        """ Assign External ID as Reference"""
        # invoices = self.env['account.invoice'].browse(context['active_ids'])
        invoices = self.env['account.invoice'].search([])
        for invoice in invoices:
            invoice_model = invoice.get_external_id()[invoice.id]
            if invoice_model:
                invoice_model = invoice_model.split('.')
                invoice.number = invoice_model[1].lstrip('CI_')

    def create_credit_notes(self):
        """Remove prduct name in description sale."""
        context = dict(self._context or {})
        invoices = self.env['account.invoice'].browse(context['active_ids'])
        # invoices = self.env['account.invoice'].search([])
        for invoice in invoices:
            if invoice.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
                invoice.type = 'out_refund'
                for invoice_line in invoice.invoice_line_ids:
                    if invoice_line.quantity < 0:
                        invoice_line.quantity = invoice_line.quantity * -1
                    if invoice_line.price_unit < 0:
                        invoice_line.price_unit = invoice_line.price_unit * -1

    def validate_invoice(self):
        context = dict(self._context or {})
        invoices = self.env['account.invoice'].browse(context['active_ids'])
        # invoices = self.env['account.invoice'].search([])
        for invoice in invoices:
            invoice.action_invoice_open()
