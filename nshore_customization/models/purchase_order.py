# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_notes(self):
        for purchase in self:
            if purchase.notes:
                purchase.note = purchase.notes[0:10] + "..."

    note = fields.Text(string='Notes', compute='_get_notes')
