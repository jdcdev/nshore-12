# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountPrintStatement(models.TransientModel):
    """Added new module for sending mail."""

    _name = "account.print.customer.statement"
    _description = "Account Print Customer Statements"
    # _rec_name = 'partner_ids'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    partner_ids = fields.Many2many('res.partner', string='Customer')
    company_id = fields.Many2one(
        'res.company', String="Company",
        default=lambda self: self.env.user.company_id)

    @api.multi
    def send_print_customer_statement(self):
        """For sending e-mail to multiple partners."""
        data = self.read([
            'start_date',
            'end_date',
        ])[0]
        data_dict = {}
        start_date = data['start_date']
        end_date = data['end_date']
        ctx = {
            'start_date': start_date,
            'end_date': end_date
        }
        if start_date > end_date:
            raise UserError(
                _("Start date should not be greater than end date"))
        else:
            template_id = self.env.ref(
                'nshore_customization.email_template_partner_statement')
            if template_id:
                invoice_ids = self.env['account.invoice'].search([
                    ('state', '!=', 'draft'),
                    ('date_invoice', '>=', start_date),
                    ('date_invoice', '<=', end_date),
                    ('type', '=', 'out_invoice')])
                partner_list = [inv.partner_id for inv in invoice_ids]
                partner_ids = list(set(partner_list))
                email_partner_list = [partner for partner in partner_ids if partner.email]
                partner_list = [partner.id for partner in partner_ids if not partner.email]
                for email_partner in email_partner_list:
                    template_id.write({'email_to': email_partner.email})
                    template_id.with_context(ctx).send_mail(email_partner.id, force_send=False)
                if partner_list:
                    data_dict = {
                        'partner_ids': list(set(partner_list)),
                        'start_date': start_date,
                        'end_date': end_date
                    }
                    return self.env.ref(
                        'nshore_customization.custom_customer_statement'
                    ).report_action(data=data_dict, docids=self.id)

    @api.multi
    def print_customer_statement(self):
        """It creates pdf reports for particular partner."""
        data_dict = {}
        partner_list = []
        if self.start_date > self.end_date:
            raise UserError(
                _("Start date should not be greater than end date"))
        data = self.read([
            'start_date',
            'end_date'
        ])[0]
        start_date = data['start_date']
        end_date = data['end_date']
        partner_list = self.partner_ids.ids
        data_dict.update({
            'partner_ids': list(set(partner_list)),
            'start_date': start_date,
            'end_date': end_date
        })
        return self.env.ref(
            'nshore_customization.custom_customer_statement'
        ).report_action(self, data_dict)
