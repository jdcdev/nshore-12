# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    """Class inherit to add field."""

    _inherit = 'res.users'

    # added salesperson for domain filter in other fields.
    is_salesperson = fields.Boolean(string="Is Sales Person?")
