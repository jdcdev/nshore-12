# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools import float_compare
from odoo.exceptions import ValidationError


class InventoryAdjustment(models.Model):
    """Added new module import Inventory adjustment."""

    _name = "inventory.adjustment.products"
    _description = "Products Inventory Adjustment"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reason', required=True)
    user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string="Sales Person")
    from_location = fields.Many2one(
        'stock.location', string="Source Location", required=True,
        domain=[('usage', '=', 'internal')])
    to_location = fields.Many2one(
        'stock.location', string="Destination Location", required=True,
        domain=[('usage', '=', 'customer')])
    line_ids = fields.One2many(
        'inventory.adj.product.line', 'adjustment_id',
        string="Products to Import")

    @api.multi
    def update_qty_adjustment(self):
        """Function call to create moves."""
        if not self.line_ids:
            raise ValidationError(_('Please Select Product to Import.'))
        for line in self.line_ids:
            moves = {
                'name': self.name + line.product_id.product_ref,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty_sub,
                'product_uom': line.product_uom_id.id,
                'location_id': self.from_location.id,
                'location_dest_id': self.to_location.id,
                'warehouse_id': self.from_location.get_warehouse().id}
            final_move = self.env['stock.move'].create(moves)
            final_move._action_confirm()
            final_move.update({'quantity_done': line.qty_sub})
            final_move._action_assign()
            final_move._action_done()


class InventoryAdjustmentProducts(models.Model):
    """Added new module import Inventory adjustment."""

    _name = "inventory.adj.product.line"

    @api.model
    def _default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id')

    product_id = fields.Many2one('product.product')
    qty_sub = fields.Float(string="Quantity", default=1.0)
    adjustment_id = fields.Many2one('inventory.adjustment.products')
    product_uom_id = fields.Many2one(
        'uom.uom', string='Unit of Measure',
        required=True, readonly=True, default=_default_product_uom_id)

    @api.onchange('product_id', 'qty_sub')
    def _onchange_product_id_check_qty(self):
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            product = self.product_id
            product_qty = self.product_uom_id._compute_quantity(
                self.qty_sub, self.product_id.uom_id)
            if float_compare(product.qty_available, product_qty, precision_digits=precision) == -1:
                message = _('You plan to sell %s %s of %s but you only have %s %s available in %s warehouse.') % \
                    (self.qty_sub, self.product_uom_id.name,
                        self.product_id.name, product.qty_available,
                        product.uom_id.name,
                        self.adjustment_id.from_location.name)
                # We check if some products are available in other warehouses.
                if float_compare(product.qty_available, self.product_id.qty_available, precision_digits=precision) == -1:
                    message += _('\nThere are %s %s available across all warehouses.\n\n') % \
                        (self.product_id.qty_available, product.uom_id.name)
                    for warehouse in self.env['stock.warehouse'].search([]):
                        quantity = self.product_id.with_context(
                            warehouse=warehouse.id).qty_available
                        if quantity > 0:
                            message += "%s: %s %s\n" % (warehouse.name, quantity, self.product_id.uom_id.name)
                warning_mess = {
                    'title': _('Not enough inventory!'),
                    'message': message
                }
                return {'warning': warning_mess}
        return {}
