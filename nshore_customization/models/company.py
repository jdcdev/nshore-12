# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    """Class Inherit to change over due report."""

    _inherit = "res.company"

    @api.model
    def _default_overdue_msg(self):
        message_overdue = '''Here is your open balance report, please remit payment at your earliest convenience, we appreciate your business

Thank you'''
        return message_overdue

    overdue_msg = fields.Text(
        string='Overdue Payments Message', translate=True,
        default=_default_overdue_msg)
