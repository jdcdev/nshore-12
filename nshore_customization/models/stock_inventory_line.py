# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"
    _order = 'name, product_id'

    # Added products name related field to order lines by product name and id
    name = fields.Char("Name", related="product_id.name")