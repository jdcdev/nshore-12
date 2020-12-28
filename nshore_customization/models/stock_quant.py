# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    reserved_quantity = fields.Float(
        'Reserved Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.0,
        help='Quantity of reserved products in this quant, in the default unit of measure of the product',
        readonly=True, required=True)

    quantity = fields.Float(
        'Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        help='Quantity of products in this quant, in the default unit of measure of the product',
        readonly=True, required=True, oldname='qty')