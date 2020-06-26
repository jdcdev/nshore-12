from odoo import fields, models, api


class ReturnReason (models.Model):
    _name = 'return.reason'
    _description = 'Return Reason'

    name = fields.Char(string="Reason Name")
    


