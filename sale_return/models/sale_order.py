from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale Order'

    state = fields.Selection(selection_add=[('return', 'Returned')])

    @api.multi
    def show_return(self):
        return {
        'name': ('Return Order'), 
        'view_type': 'form', 
        'view_mode': 'tree', 
        'res_model': 'return.order', 
        'type': 'ir.actions.act_window',

      }

    def action_return_order(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'return.order',
            'view_id': self.env.ref('sale_return.view_return_order_form').id,
            'type': 'ir.actions.act_window',
            'views': [(False, 'form')],
            'context': {'default_partner_id':self.partner_id.id or False, 'default_sale_order_id':self.id or False},
            'target': 'current',
        }

# class ReturnOrder(models.Model):
#     _inherit = 'return.order'
#     _description = 'Return Order'

    # @api.model
    # def default_get(self, fields):
    #     rec = super(ReturnOrder, self).default_get(fields)
    #     active_id= self._context.get('active_id')
    #     if active_id:
    #         active_model = self._context.get('active_model')
    #         sale_order = self.env[active_model].browse(active_id)
    #         rec['partner_id'] = sale_order.partner_id.id
    #         sale_order_id = self.env['ir.config_parameter'].sudo().set_param('sale.order.id', active_id)
    #         return rec


class ReturnOrderLine(models.Model):
    _inherit = 'return.order.line'
    _description = 'Return Order Line'

    def _default_sale_order_id(self):
        return int (self.env['ir.config_parameter'].sudo().get_param('sale.order.id'))

    sale_order_id = fields.Many2one('sale.order', string='Sale Order',default=_default_sale_order_id)