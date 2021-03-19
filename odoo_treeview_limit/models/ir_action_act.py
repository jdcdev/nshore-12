# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IrActionsActWindow(models.Model):
    """Class Inherit to extend the limit of records."""

    _inherit = 'ir.actions.act_window'

    def _limit_records(self):
        for l in self:
            l.limit = self.env.user.company_id.tree_limit

    limit = fields.Integer(
        compute=_limit_records, help='Default limit for the list view')
