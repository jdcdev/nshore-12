# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()

        if self.invoice_id.type not in ['out_invoice', 'out_refund']:
            return res

        partner = self.invoice_id.partner_id
        pricelist = self.invoice_id.pricelist_id
        product = self.product_id

        if not partner or not product or not pricelist:
            return res

        inv_date = self.invoice_id.date_invoice or date.today().strftime(DT)
        product = product.with_context(
            lang=partner.lang,
            partner=partner.id,
            quantity=self.quantity,
            date=inv_date,
            pricelist=pricelist.id,
            uom=self.uom_id.id
        )
        self.price_unit = self.env['account.tax']._fix_tax_included_price(
            product.price,
            product.taxes_id,
            self.invoice_line_tax_ids
        )
        return res

    @api.model
    def create(self, vals):
        res = super(AccountInvoiceLine, self).create(vals)
        company_id = res.company_id or self.env.user.company_id
        if 'invoice_line_tax_ids' not in vals:
            if res.invoice_id.type in ('out_invoice', 'out_refund'):
                taxes = res.product_id.taxes_id.filtered(lambda r: r.company_id == company_id) or res.account_id.tax_ids or res.invoice_id.company_id.account_sale_tax_id
            else:
                taxes = res.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == company_id) or res.account_id.tax_ids or res.invoice_id.company_id.account_purchase_tax_id
            res.invoice_line_tax_ids = res.invoice_id.fiscal_position_id.map_tax(taxes, res.product_id, res.invoice_id.partner_id)
            # Call compute method for tax
            res._compute_price()
        res.invoice_id._onchange_invoice_line_ids()
        res.invoice_id.res._compute_amount()
        return res

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        res = super(AccountInvoiceLine, self)._onchange_uom_id()
        if self.invoice_id.type not in ['out_invoice', 'out_refund']:
            return res

        partner = self.invoice_id.partner_id
        pricelist = self.invoice_id.pricelist_id
        product = self.product_id

        if not partner or not product or not pricelist:
            return res

        inv_date = self.invoice_id.date_invoice or date.today().strftime(DT)
        product = product.with_context(
            lang=partner.lang,
            partner=partner.id,
            quantity=self.quantity,
            date=inv_date,
            pricelist=pricelist.id,
            uom=self.uom_id.id
        )
        self.price_unit = self.env['account.tax']._fix_tax_included_price(
            product.price,
            product.taxes_id,
            self.invoice_line_tax_ids
        )
        return res