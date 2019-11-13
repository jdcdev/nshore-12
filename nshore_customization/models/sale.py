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