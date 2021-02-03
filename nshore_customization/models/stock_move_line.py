# -*- coding: utf-8 -*-

from odoo import fields, models

class StockQuant(models.Model):
    _inherit = 'stock.move.line'
    
    # added field to get name of customer/vendor in move.
    partner_id = fields.Many2one(
        'res.partner', 'Customer/Vendor', related="picking_id.partner_id")