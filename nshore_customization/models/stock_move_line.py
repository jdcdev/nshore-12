# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class StockMOveLine(models.Model):
    """Inherited class to add partner and product OnHandQty."""

    _inherit = 'stock.move.line'

    # added field to get name of customer/vendor in move.
    partner_id = fields.Many2one(
        'res.partner', 'Customer/Vendor', related="picking_id.partner_id")
    product_onhand_qty = fields.Char(
        'Initial On-hand Qty', default='0')

    @api.model_create_multi
    def create(self, vals_list):
        """Function Inherit to get early product on hand qty."""
        for vals in vals_list:
            if 'qty_done' in vals:
                product = self.env['product.product'].browse(
                    vals['product_id'])
                vals['product_onhand_qty'] = str(product.qty_available)
        return super(StockMOveLine, self).create(vals_list)

    @api.multi
    def write(self, values):
        """Messsage post when done qty change."""
        if 'qty_done' in values:
            self.product_onhand_qty = str(self.product_id.qty_available)
            for line in self:
                line._update_line_quantity(values)
        return super(StockMOveLine, self).write(values)

    def _update_line_quantity(self, values):
        """Fucntion call to add message in chatter when done qty change."""
        picking = self.mapped('picking_id')
        for pick in picking:
            po_lines = self.filtered(lambda x: x.picking_id == pick)
            msg = "<b>The Done Quantity has been updated.</b><ul>"
            for pick in po_lines:
                msg += "<li> %s:" % (pick.product_id.display_name,)
                msg += "<br/>" + _("Done") + ": %s -> %s <br/>" % (
                    pick.qty_done, float(values['qty_done']),)
            msg += "</ul>"
            picking.message_post(body=msg)
