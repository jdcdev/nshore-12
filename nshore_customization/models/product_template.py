# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    net_cost = fields.Float(string='Net Cost')
    product_ref = fields.Char(string='Product Reference')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):
        return [(product.id, '%s' % (product.name)) for product in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        context = self.env.context
        domain = []
        if args is None:
            args = []
        if context and context.get('product_search', False) and name:
            domain = [('product_tmpl_id.default_code', operator, name)]
            products = self.search(domain + args, limit=limit)
        if domain:
            domain = ['|', '|',
                      ('product_tmpl_id.product_ref', operator, name),
                      ('product_tmpl_id.name', operator, name),
                      ('product_tmpl_id.description', operator, name)]
            if products:
                products += self.search(domain + args, limit=limit)
            else:
                self.search(domain + args, limit=limit)
            return products.name_get()
        return super(ProductProduct, self).name_search(name, args=args, operator=operator, limit=limit)


class PricelistItem(models.Model):

    _inherit = "product.pricelist.item"

    base = fields.Selection(selection_add=[('net_cost', 'Net Cost')])


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.multi
    def print_report(self):
        data = {}
        categories = self.search([])
        data['categories'] = categories
        datas = {
            'ids': categories.ids,
            'model': 'product.category',
            'form': data,
        }
        return self.env.ref('nshore_customization.action_report_inventory_listing').report_action(categories, data=datas)
