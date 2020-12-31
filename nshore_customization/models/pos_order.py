# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class PosOrder(models.Model):
    _inherit = 'pos.order'

    qty = fields.Float('Quantity', digits=dp.get_precision(
        'Product Unit of Measure'), default=1)
