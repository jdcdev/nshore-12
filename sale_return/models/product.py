from odoo import fields, models, api


class ProductProduct (models.Model):
    _inherit = 'product.product'
    _description = 'Product'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        product_list = []
        if args is None:
            args = []
        if self._context.get('sale_order_id'):
            sale_order_rec = self.env['sale.order'].browse(
                self._context.get('sale_order_id'))
            for line in sale_order_rec:
                for line in line.order_line:
                    product_list.append(line.product_id.id)
            args.append(('id', 'in', product_list))
        return super(ProductProduct, self).name_search(
            name, args, operator, limit)
