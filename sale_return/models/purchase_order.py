from odoo import fields, models, api


class PurchaseOrder(models.Model):
    """Class inherit to add return order functionality."""

    _inherit = 'purchase.order'
    _description = 'Purchase Order'

    state = fields.Selection(selection_add=[('return', 'Returned')])

    @api.multi
    def show_return(self):
        """Function call to show return orders."""
        return {
            'name': ('Return Order'),
            'view_type': 'form',
            'domain': [('purchase_ids', '=', self.ids)],
            'view_mode': 'tree,form',
            'res_model': 'return.order',
            'type': 'ir.actions.act_window',
            'context': {
                'default_supplier_id': self.partner_id.id or False,
                'default_type_partner': 'supplier' or False}}
