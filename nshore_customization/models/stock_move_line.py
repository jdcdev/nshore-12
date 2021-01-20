# -*- coding: utf-8 -*-

from odoo import fields, models

class StockQuant(models.Model):
    _inherit = 'stock.move.line'
    
    partner_id = fields.Many2one(
        'res.partner', 'Customer/Vendor', related="move_id.partner_id")