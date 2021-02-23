# -*- coding: utf-8 -*-

from odoo import api, models


class IrFilters(models.Model):
    """Class Inherit to add condition on _check_global_default."""

    _inherit = 'ir.filters'
    _description = 'Filters'

    @api.model
    def _check_global_default(self, vals, matching_filters):
        if self.env.user.company_id.default_share_with_user:
            return
        raise super(IrFilters, self)._check_global_default(
            vals, matching_filters)
