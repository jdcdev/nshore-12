from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models


class InventoryValuationReport(models.AbstractModel):
    _name = 'report.nshore_customization.report_inventory_valuation'

    _description = 'Report Inventory Valuation'

    def get_product_details(self, categories):
        product_data = []
        products = self.env['product.product']
        for product in products.search([
            ('categ_id', '=', categories.id),
                ('qty_available', '!=', 0.0)]):
            dict = {
                'id': product.default_code,
                'ref': product.product_ref,
                'description': product.name,
                'cost': product.standard_price or 0,
                'net_cost': product.net_cost or 0,
                'list': product.lst_price or 0,
                'location_onhand': product.qty_available or 0,
                'location': [],
            }
            # reordering = False
            # for rule in reorder.search([('product_id', '=', product.id)]):
            #     reordering = True
            #     dict.update({
            #         'reorder': rule.product_min_qty or 0,
            #         'max': rule.product_max_qty or 0,
            #     })
            #     if rule.location_id:
            #         location_dict = {
            #             'location_name': rule.location_id.name,
            #             'location_max': rule.product_max_qty or 0,
            #             'location_reorder': rule.product_min_qty or 0,
            #         }
            #         quants = self.env['stock.quant'].search(
            #             [('product_id', '=', product.id),
            #              ('location_id', '=', rule.location_id.id)])
            #         for quant in quants:
            #             location_dict.update(
            #                 {'location_onhand': quant.quantity or 0})
            #         if not quants:
            #             location_dict.update({'location_onhand': 0})
            #         dict['location'].append(location_dict)
            # if reordering:
            product_data.append(dict)
        return product_data

    @api.model
    def _get_report_values(self, docids, data=None):
        docids = self.env['product.category'].search([]).ids
        docs = self.env['product.category'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'product.category',
            'docs': docs,
            'product_data': self.get_product_details,
            'date': datetime.now().strftime('%m/%d/%Y'),
        }
