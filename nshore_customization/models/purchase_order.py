# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_notes(self):
        for purchase in self:
            if purchase.notes:
                purchase.note = purchase.notes[0:15] + "..."

    note = fields.Text(string='Notes', compute='_get_notes')
