# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    """Class inherit to add field."""

    _inherit = 'res.users'

    is_salesperson = fields.Boolean(string="Is Sales Person?")
