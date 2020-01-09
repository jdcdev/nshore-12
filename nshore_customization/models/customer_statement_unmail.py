from odoo import models, fields


class CustomerStatementUnmail(models.Model):
    _name = "customer.statement.unmail"
    _description = "Customer Statement without Mail"

    date = fields.Datetime(string="Date")
    partner_ids = fields.Many2many("res.partner",
                                   "customer_statement_unmail_partner_rel",
                                   string="Customer")
    attachment_id = fields.Many2one("ir.attachment", string="Report")
