# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class StockQuant(models.Model):
    _inherit = 'stock.move.line'

    # added field to get name of customer/vendor in move.
    partner_id = fields.Many2one(
        'res.partner', 'Customer/Vendor', related="picking_id.partner_id")

    @api.multi
    def write(self, values):
        """Messsage post when done qty change."""
        if 'qty_done' in values:
            for line in self:
                line._update_line_quantity(values)
        return super(StockQuant, self).write(values)

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
