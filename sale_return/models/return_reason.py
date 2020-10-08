from odoo import fields, models, api


class ReturnReason (models.Model):
    """Class added for return reason."""

    _name = 'return.reason'
    _description = 'Return Reason'

    name = fields.Char(string="Reason Name")
