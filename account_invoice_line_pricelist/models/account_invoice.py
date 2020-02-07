# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    pricelist_id = fields.Many2one(
        'product.pricelist',
        'Pricelist',
        help='Pricelist for current invoice.'
    )

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.type in ['out_invoice', 'out_refund']:
            self.pricelist_id = None
            if self.partner_id:
                self.pricelist_id = self.partner_id.property_product_pricelist
        return res

    @api.model
    def create(self, vals):
        if 'pricelist_id' not in vals and 'partner_id' in vals:
            partner_id = self.env['res.partner'].browse(vals['partner_id'])
            if partner_id and partner_id.property_product_pricelist:
                vals.update({'pricelist_id': partner_id.property_product_pricelist.id})
        res = super(AccountInvoice, self).create(vals)
        return res
