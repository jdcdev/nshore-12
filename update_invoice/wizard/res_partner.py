# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductExternalID(models.TransientModel):
    _name = 'partner.name'

    def update_name(self):
        for partner in self.env['res.partner'].search([]):
            if partner.name:
                partner.update({
                    'name': partner.name.replace('_', ' ').title()
                    })
