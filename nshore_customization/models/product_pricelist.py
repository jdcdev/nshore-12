# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PricelistItem(models.Model):
    """Class inherit to add field."""
    _inherit = "product.pricelist.item"

    base = fields.Selection(selection_add=[('net_cost', 'Net Cost')])


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    @api.model
    def _name_search(
            self, name, args=None, operator='ilike', limit=100,
            name_get_uid=None):
        return super(Pricelist, self)._name_search(
            name, args, operator=operator, limit=25000,
            name_get_uid=name_get_uid)
