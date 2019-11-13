# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import datetime


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

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        """When the date will change it will display the list of partners."""
        if self.start_date and self.end_date:
            final_start_date = datetime.date.today()
            final_end_date = datetime.date.today()
            start_date = datetime.datetime.strptime(
                str(self.start_date), "%Y-%m-%d").date()
            date_start_format = start_date.strftime("%d/%m/%Y")
            final_start_date = datetime.datetime.strptime(
                str(date_start_format), "%d/%m/%Y").date()
            end_date = datetime.datetime.strptime(
                str(self.end_date), "%Y-%m-%d").date()
            date_end_format = end_date.strftime("%d/%m/%Y")
            final_end_date = datetime.datetime.strptime(
                str(date_end_format), "%d/%m/%Y").date()
            invoice = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice')])
            payment = self.env['account.payment'].search([])
            partner_list = []
            for invoices in invoice:
                if invoices.date_invoice:
                    invoices_date = datetime.datetime.strptime(
                        str(invoices.date_invoice), "%Y-%m-%d").date()
                    invoices_date_format = invoices_date.strftime("%d/%m/%Y")
                    final_invoices_date = datetime.datetime.strptime(
                        str(invoices_date_format), "%d/%m/%Y").date()
                    if final_start_date <= final_invoices_date <= final_end_date:
                        partner_list.append(invoices.partner_id.id)
            for payments in payment:
                if payments.payment_date:
                    payments_date = datetime.datetime.strptime(
                        str(payments.payment_date), "%Y-%m-%d").date()
                    payments_date_format = payments_date.strftime("%d/%m/%Y")
                    final_payment_date = datetime.datetime.strptime(
                        str(payments_date_format), "%d/%m/%Y").date()
                    if final_start_date <= final_payment_date <= final_end_date:
                        partner_list.append(payments.partner_id.id)
            self.partner_ids = partner_list

    @api.multi
    def send_print_customer_statement(self):
        """For sending e-mail to multiple partners."""
        if self.start_date > self.end_date:
            raise UserError(
                _("Start date should not be greater than end date"))
        else:
            template_id = self.env.ref(
                'nshore_customization.email_template_partner_statement')
            if template_id:
                # base_context = self.env.context
                for partner in self.partner_ids:
                    partner.sudo().write({
                        'invoice_start_date': self.start_date,
                        'invoice_end_date': self.end_date
                    })
                    if partner.email:
                        template_id.write({'email_to': partner.email})
                        template_id.send_mail(partner.id, force_send=True)
                    else:
                        return self.env.ref(
                            'nshore_customization.custom_customer_statement'
                        ).report_action(
                            partner)

    @api.multi
    def print_customer_statement(self):
        """It creates pdf reports for particular partner."""
        final_partners_list = []
        if self.start_date > self.end_date:
            raise UserError(
                _("Start date should not be greater than end date"))
        else:
            for partner in self.partner_ids:
                account_record = self.env['account.invoice'].search(
                    [('partner_id', '=', partner.id)])
                # payment_record = self.env['account.payment'].search(
                #     [('partner_id', '=', partner.id)])
                for account in account_record:
                    values = [account.partner_id,
                              account.partner_shipping_id]
                    final_partners_list.append({partner.name: values})
            return self.env.ref(
                'nshore_customization.custom_customer_statement'
            ).report_action(self)
        # for payment in payment_record:
        #     print(payment.partner_id.name)
