from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.partner_id and self.partner_id.child_ids:
            default_invoice_child = self.partner_id.child_ids.filtered(lambda x: x.default_delivery == True)
            if default_invoice_child:
                self.partner_shipping_id = default_invoice_child.id
