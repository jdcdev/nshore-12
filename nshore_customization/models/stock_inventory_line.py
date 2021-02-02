# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"
    _order = 'name, product_id'

    name = fields.Char("Name", related="product_id.name")