# -*- coding: utf-8 -*-

from odoo import models, api


class UpdatePricelistItems(models.TransientModel):
    """Added new module import Inventory adjustment."""

    _name = 'update.product.pricelist.item'

    @api.multi
    def update_pricelist_item(self):
        """Update Pricelist Item from fixed to formula."""
        active_ids = self.env.context.get('active_ids')
        price_list = self.env['product.pricelist'].browse(active_ids)
        for pricelist in price_list:
            for items in pricelist.item_ids.filtered(
                    lambda l: l.compute_price == 'fixed'):
                cost_price = 0.0
                # Get Product or Template cost price 
                if items.product_id:
                    cost_price = items.product_id.standard_price
                elif items.product_tmpl_id:
                    cost_price = items.product_tmpl_id.standard_price
                # Get formula value
                formula = final_formula = 0.0
                formula = items.fixed_price - cost_price
                formula = formula / cost_price
                formula = formula * 100
                if formula < 0:
                    final_formula = formula
                else:
                    final_formula = - formula
                # Update pricelist item from fixed to formula.
                items.update({
                    'compute_price': 'formula',
                    'base': 'standard_price',
                    'price_discount': final_formula
                })
