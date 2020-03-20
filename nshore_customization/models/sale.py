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
            self.action_confirm()
            self.action_invoice_create()
            delivery_obj = self.env['stock.picking'].search([('group_id.name', '=', self.name),('state', '!=', 'cancel')])
            invoice_obj = self.env['account.invoice'].search([('origin', '=', self.name)])
            for order_line in self.order_line:
                if delivery_obj:
                    [picking_line.update({
                            'quantity_done': order_line.product_uom_qty,
                            }) for picking_line in delivery_obj.move_lines]
            delivery_obj.button_validate()
            if invoice_obj:
                invoice_obj.action_invoice_open()
            return invoice_obj

    def return_invoice(self):
        invoice_obj  = self.express_checkout()
        tree_view_ref = self.env.ref('account.invoice_tree_with_onboarding',False)
        form_view_ref = self.env.ref('account.invoice_form',False)
        return {
                'name':'Account Invoice',
                'res_model':'account.invoice',
                'view_type':'form',
                'view_mode':'tree, form',
                'target':'current',
                'domain':[('id','=',invoice_obj.id)],
                'type':'ir.actions.act_window',
                'views': [(tree_view_ref and tree_view_ref.id or False,'tree'),(form_view_ref and form_view_ref.id or False,'form')],
                }


