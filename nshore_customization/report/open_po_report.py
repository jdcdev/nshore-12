from odoo import api, models, fields
from datetime import datetime


class OpenPoReport(models.AbstractModel):
    """Class call to add open po report."""

    _name = 'report.nshore_customization.report_open_po'

    def get_po_line_details(self, data, date_format):
        """Get Purchase order line details."""
        partner_dict = {}
        start_date = data['start_date']
        end_date = data['end_date']
        partner_obj = self.env['res.partner']
        purchase_order = self.env['purchase.order']
        purchase_line_vals = {}
        if data['catgeory_partner'] == 'partner':
            if data['all_vendor']:
                all_partner_ids = partner_obj.search([])
                for partner in all_partner_ids:
                    purchase_data = purchase_order.search(
                        [('partner_id', '=', partner.id),
                            ('date_order', '>=', start_date),
                            ('date_order', '<=', end_date),
                            ('state', 'not in', ['purchase', 'cancel'])])
                    for purchase in purchase_data:
                        for line in purchase.order_line:
                            purchase_line_vals = {
                                'date': purchase.date_order.date(),
                                'purchase_order': purchase.name,
                                'product': line.product_id.name,
                                'categ_id': line.product_id.categ_id.complete_name,
                                'product_qty': line.product_qty,
                                'qty_received': line.qty_received
                            }
                            if partner not in partner_dict.keys():
                                partner_dict.update({
                                    partner: {
                                        'order_line': [purchase_line_vals],
                                    }
                                })
                            else:
                                partner_dict[partner]['order_line'].append(
                                    purchase_line_vals)
                            new_dict = {'categ_partner': data['catgeory_partner']}
                            partner_dict[partner].update(new_dict)
            if not data['all_vendor']:
                partner_ids = self.env['res.partner'].browse(
                    data['partner_ids'])
                for partner in partner_ids:
                    purchase_data = purchase_order.search(
                        [('partner_id', '=', partner.id),
                            ('date_order', '>=', start_date),
                            ('date_order', '<=', end_date),
                            ('state', 'not in', ['purchase', 'cancel'])])
                    for purchase in purchase_data:
                        for line in purchase.order_line:
                            purchase_line_vals = {
                                'date': purchase.date_order.date(),
                                'purchase_order': purchase.name,
                                'product': line.product_id.name,
                                'categ_id': line.product_id.categ_id.complete_name,
                                'product_qty': line.product_qty,
                                'qty_received': line.qty_received
                            }
                            if partner not in partner_dict.keys():
                                partner_dict.update({
                                    partner: {
                                        'order_line': [purchase_line_vals],
                                    }
                                })
                            else:
                                partner_dict[partner]['order_line'].append(
                                    purchase_line_vals)
                            new_dict = {'categ_partner': data['catgeory_partner']}
                            partner_dict[partner].update(new_dict)
        if data['catgeory_partner'] == 'category':
            categ_ids = self.env['product.category'].browse(
                data['category_ids'])
            for category in categ_ids:
                partner = category
                purchase_order_line = self.env['purchase.order.line'].search(
                    [('order_id.date_order', '>=', start_date),
                        ('order_id.date_order', '<=', end_date),
                        ('product_id.categ_id', '=', category.id),
                        ('order_id.state', 'not in', ['purchase', 'cancel'])])
                for line in purchase_order_line:
                    purchase_line_vals = {
                        'date': line.order_id.date_order.date(),
                        'purchase_order': line.order_id.name,
                        'product': line.product_id.name,
                        'categ_id': line.product_id.categ_id.complete_name,
                        'product_qty': line.product_qty,
                        'qty_received': line.qty_received
                    }
                    if partner not in partner_dict.keys():
                        partner_dict.update({
                            partner: {
                                'order_line': [purchase_line_vals],
                            }
                        })
                    else:
                        partner_dict[partner]['order_line'].append(
                            purchase_line_vals)
                    new_dict = {'categ_partner': data['catgeory_partner']}
                    partner_dict[partner].update(new_dict)
        return partner_dict

    @api.model
    def _get_report_values(self, docids, data=None):
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        categ_ids = partner_ids = None
        data.update(self._context)
        if data.get('catgeory_partner') == 'partner':
            partner_ids = data.get('partner_ids')
        elif data.get('catgeory_partner') == 'category':
            categ_ids = data.get('category_ids')
        lines_data = self.get_po_line_details(data, date_format)
        return {
            'doc_ids': docids,
            'doc_model': 'purchase.order',
            'docs_partner': self.env['res.partner'].browse(partner_ids),
            'docs_categ': self.env['product.category'].browse(categ_ids),
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
        }
