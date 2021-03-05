# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


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

    @api.multi
    def write(self, values):
        """Messsage post when qty change."""
        if 'product_qty' in values:
            for line in self:
                line._update_line_quantity(values)
        return super(InventoryLine, self).write(values)

    def _update_line_quantity(self, values):
        """Fucntion call to add message in chatter when qty change."""
        inventory = self.mapped('inventory_id')
        for inv in inventory:
            inv_lines = self.filtered(lambda x: x.inventory_id == inventory)
            msg = "<b>The Real quantity has been updated.</b><ul>"
            for line in inv_lines:
                msg += "<li> %s:" % (line.product_id.display_name,)
                msg += "<br/>" + _("Real Quantity") + ": %s -> %s <br/>" % (
                    line.product_qty, float(values['product_qty']),)
            msg += "</ul>"
            inventory.message_post(body=msg)
