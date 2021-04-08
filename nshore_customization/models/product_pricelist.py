# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PricelistItem(models.Model):
    """Class inherit to add field."""

    _inherit = "product.pricelist.item"
    _order = 'name asc'

    base = fields.Selection(selection_add=[('net_cost', 'Net Cost')])
    name = fields.Char(
        'Name', compute='_get_pricelist_item_name_price',
        help="Explicit rule name for this pricelist line.", store=True)
    old_fixed_price = fields.Float(string="Old Fixed")
    price_discount = fields.Float('Price Discount', default=0, digits=(16, 6))


class Pricelist(models.Model):
    """Class Inherit to added name serach for limit."""

    _inherit = "product.pricelist"

    @api.model
    def _name_search(
            self, name, args=None, operator='ilike', limit=100,
            name_get_uid=None):
        return super(Pricelist, self)._name_search(
            name, args, operator=operator, limit=25000,
            name_get_uid=name_get_uid)
