# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_notes(self):
        for purchase in self:
            if purchase.notes:
                purchase.note = purchase.notes[0:15] + "..."

    note = fields.Text(string='Notes', compute='_get_notes')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        # Function override to get unit price while qty is in minus.
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)
        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            # When products qty is in minus, passing net cost ot unit price.
            if self.product_qty < 0:
                self.price_unit = self.product_id.net_cost
            # Closed based condition to achive above one.a
            # if self.product_id.seller_ids.filtered(lambda s: s.name.id == self.partner_id.id):
            #     self.price_unit = 0.0
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
        self.price_unit = price_unit