# -*- coding: utf-8 -*-

from odoo import fields, models


class StockInv(models.Model):
    """Inherit Stock Inventory to add mail thread."""
    _name = 'stock.inventory'
    _inherit = ['stock.inventory', 'mail.thread', 'mail.activity.mixin']


class InventoryLine(models.Model):
    """Inherit Inventory Line module to add order."""

    _inherit = "stock.inventory.line"
    _order = 'name, product_id'

    # Added products name related field to order lines by product name and id
    name = fields.Char("Name", related="product_id.name")
