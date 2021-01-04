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
