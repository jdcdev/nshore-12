# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    """Class inherit to add some net cost fields."""

    _inherit = 'product.template'
    _order = 'name'

    net_cost = fields.Float(string='Net Cost', digits=dp.get_precision('Product Price'))
    product_ref = fields.Char(string='Product Reference')
    list_price = fields.Float(
        'Sales Price', default=1.0,
        digits=dp.get_precision('Product Price'),
        help="Price at which the product is sold to customers.")
    # lst_price: catalog price for template, but including extra for variants
    lst_price = fields.Float(
        'Public Price', related='list_price', readonly=False,
        digits=dp.get_precision('Product Price'))
    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits=dp.get_precision('Product Price'), groups="base.group_user",
        help="Cost used for stock valuation in standard price and as a first price to set in average/FIFO.")

    def _update_price_values(self, values):
        """Fucntion call to add message in chatter when qty change."""
        msg = '<ul>'
        if values.get('list_price'):
            msg += "<li> %s:" % (self.name,)
            msg += "<br/>" + _("Sales Price") + ": %s -> %s <br/>" % (
                self.list_price, float(values['list_price']),)
        if values.get('lst_price'):
            msg += "<li> %s:" % (self.name,)
            msg += "<br/>" + _("Sales Price") + ": %s -> %s <br/>" % (
                self.lst_price, float(values['lst_price']),)
        if values.get('standard_price'):
            msg += "<li> %s:" % (self.name,)
            msg += "<br/>" + _("Cost") + ": %s -> %s <br/>" % (
                self.standard_price, float(values['standard_price']),)
        if values.get('net_cost'):
            msg += "<li> %s:" % (self.name,)
            msg += "<br/>" + _("Net Cost") + ": %s -> %s <br/>" % (
                self.net_cost, float(values['net_cost']),)
        self.message_post(body=msg)

    @api.multi
    def write(self, vals):
        for rec in self:
            rec._update_price_values(vals)
        tools.image_resize_images(vals)
        res = super(ProductTemplate, self).write(vals)
        if 'attribute_line_ids' in vals or vals.get('active'):
            self.create_variant_ids()
        if 'active' in vals and not vals.get('active'):
            self.with_context(active_test=False).mapped('product_variant_ids').write({'active': vals.get('active')})
        return res

class ProductProduct(models.Model):
    """Class inherit for modify some functions."""

    _inherit = 'product.product'
    _order = 'name'

    qty_at_date = fields.Float(
        'Quantity', digits=dp.get_precision('Product Unit of Measure'), compute='_compute_stock_value')

    @api.multi
    def name_get(self):
        """Function inherit to get product name with product ref."""
        return [(product.id, '%s' % (product.name)) for product in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Function call to search name of product with product ref."""
        if args is None:
            args = []
        domain = [
            '|', ('product_tmpl_id.product_ref', "=ilike", name + '%'),
            ('product_ref', "=ilike", name + '%')
        ]
        products = self.search(
            domain + args, limit=limit, order='product_ref')
        if products:
            return products.name_get()
        else:
            domain = [
                '|', ('product_tmpl_id.product_ref', "=ilike", name),
                ('product_ref', "=ilike", name)
            ]
            products = self.search(
                domain + args, limit=limit, order='product_ref')
            if products:
                return products.name_get()
            domain = [
                '|', '|', '|',
                ('product_tmpl_id.name', operator, name),
                ('product_tmpl_id.description', operator, name),
                ('name', operator, name),
                ('description', operator, name)
            ]
            products = self.search(
                domain + args, limit=limit, order='product_ref')
            if products:
                return products.name_get()
        return super(ProductProduct, self).name_search(
            name, args=args, operator=operator, limit=limit)

    @api.multi
    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value', 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation', 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        """Function override to update products price with net cost"""
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')

        real_time_product_ids = [product.id for product in self if product.product_tmpl_id.valuation == 'real_time']
        if real_time_product_ids:
            self.env['account.move.line'].check_access_rights('read')
            fifo_automated_values = {}
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IN %%s AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
            params = (tuple(real_time_product_ids), self.env.user.company_id.id)
            if to_date:
                query = query % ('AND aml.date <= %s',)
                params = params + (to_date,)
            else:
                query = query % ('',)
            self.env.cr.execute(query, params=params)

            res = self.env.cr.fetchall()
            for row in res:
                fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        product_values = {product.id: 0 for product in self}
        product_move_ids = {product.id: [] for product in self}

        if to_date:
            domain = [
                ('product_id', 'in', self.ids),
                ('date', '<=', to_date)] + StockMove._get_all_base_domain()
            value_field_name = 'value'
        else:
            domain = [('product_id', 'in', self.ids)] + StockMove._get_all_base_domain()
            value_field_name = 'remaining_value'

        StockMove.check_access_rights('read')
        query = StockMove._where_calc(domain)
        StockMove._apply_ir_rules(query, 'read')
        from_clause, where_clause, params = query.get_sql()
        query_str = """
            SELECT stock_move.product_id, SUM(COALESCE(stock_move.{}, 0.0)), ARRAY_AGG(stock_move.id)
            FROM {}
            WHERE {}
            GROUP BY stock_move.product_id
        """.format(value_field_name, from_clause, where_clause)
        self.env.cr.execute(query_str, params)
        for product_id, value, move_ids in self.env.cr.fetchall():
            product_values[product_id] = value
            product_move_ids[product_id] = move_ids

        for product in self:
            if product.cost_method in ['standard', 'average']:
                qty_available = product.with_context(
                    company_owned=True, owner_id=False).qty_available
                # changed price used with product net cost.
                price_used = product.net_cost
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_value = product_values[product.id]
                        product.qty_at_date = product.with_context(
                            company_owned=True, owner_id=False).qty_available
                        product.stock_fifo_manual_move_ids = StockMove.browse(
                            product_move_ids[product.id])
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get(
                            (product.id, valuation_account_id)) or (0, 0, [])
                        product.stock_value = value
                        product.qty_at_date = quantity
                        product.stock_fifo_real_time_aml_ids = self.env[
                            'account.move.line'].browse(aml_ids)
                else:
                    product.stock_value = product_values[product.id]
                    product.qty_at_date = product.with_context(
                        company_owned=True, owner_id=False).qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = StockMove.browse(
                            product_move_ids[product.id])
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get(
                            (product.id, valuation_account_id)) or (0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env[
                            'account.move.line'].browse(aml_ids)


class ProductCategory(models.Model):
    """Class Inherit to add report option."""

    _inherit = 'product.category'

    @api.multi
    def print_report(self):
        """Function call to print report."""
        data = {}
        categories = self.search([])
        data['categories'] = categories
        datas = {
            'ids': categories.ids,
            'model': 'product.category',
            'form': data,
        }
        return self.env.ref(
            'nshore_customization.action_report_inventory_valuation').report_action(
            categories, data=datas)
