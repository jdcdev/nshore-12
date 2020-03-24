from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_so_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'name': _('SO Lines'),
            'res_model': 'sale.order.line',
            'target': 'new',
            'domain': [('id', 'in', self.order_line.ids)],
        }

    def _get_so_line_count(self):
        for so in self:
            so.so_line_count = len(so.order_line.ids)

    so_line_count = fields.Integer(string='SO Count',
                                   compute='_get_so_line_count')

    def express_checkout(self):
        if self.state != 'sale':
            # Delivery Creation and Validation
            self.action_confirm()
            delivery_obj = self.env['stock.picking'].search([('group_id.name', '=', self.name),('state', '!=', 'cancel')])
            if delivery_obj:
                for order_line in self.order_line:
                    [picking_line.update({
                            'quantity_done': order_line.product_uom_qty,
                            }) for picking_line in delivery_obj.move_lines]
                delivery_obj.button_validate()
            # Invoice Creation and Validation
            self.action_invoice_create()
            invoice_obj = self.env['account.invoice'].search([('origin', '=', self.name),('state', '!=', 'cancel')])
            if invoice_obj:
                invoice_obj.action_invoice_open()
                # Redirect to created Invoice
                action = self.env.ref('account.action_invoice_tree1').read()[0]
                if len(invoice_obj) == 1:
                    form_view = [(self.env.ref('account.invoice_form').id, 'form')]
                    if 'views' in action:
                        action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
                    else:
                        action['views'] = form_view
                    action['res_id'] = invoice_obj.id
                else:
                    action = {'type': 'ir.actions.act_window_close'}
                return action
