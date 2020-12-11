from odoo import fields, models, api


class SaleOrder(models.Model):
    """Class inherit to add return order functionality."""

    _inherit = 'sale.order'
    _description = 'Sale Order'

    state = fields.Selection(selection_add=[('return', 'Returned')])

    @api.multi
    def show_return(self):
        """Function call to show return orders."""
        return {
            'name': ('Return Order'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'return.order',
            'type': 'ir.actions.act_window'}

    def action_return_order(self):
        """Action call for return order."""
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'return.order',
            'view_id': self.env.ref('sale_return.view_return_order_form').id,
            'type': 'ir.actions.act_window',
            'views': [(False, 'form')],
            'context': {
                'default_partner_id': self.partner_id.id or False,
                'default_sale_order_id': self.id or False},
            'target': 'current',
        }


class ReturnOrderLine(models.Model):
    """Class inherited to add sales order line info."""

    _inherit = 'return.order.line'
    _description = 'Return Order Line'

    def _default_sale_order_id(self):
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'sale.order.id'))

    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order', default=_default_sale_order_id)
