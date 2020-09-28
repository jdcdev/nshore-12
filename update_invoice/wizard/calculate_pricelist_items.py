# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class PricelistItemCount(models.TransientModel):
    """Model create for count pricelist items."""

    _name = 'calculate.pricelist.item'

    def count_pricelist_items(self):
        pricelist = self.env['product.pricelist'].search(
            [('active', '=', True)])
        item = [item.item_ids.search_count(
            [('pricelist_id', '=', item.id)]) for item in pricelist]
        _logger.info("\n\n Active Pricelist Items %s", sum(item))
