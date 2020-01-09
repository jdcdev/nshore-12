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

    # @api.onchange('start_date', 'end_date')
    # def onchange_date(self):
    #     """When the date will change it will display the list of partners."""
    #     if self.start_date and self.end_date:
    #         final_start_date = datetime.date.today()
    #         final_end_date = datetime.date.today()
    #         start_date = datetime.datetime.strptime(
    #             str(self.start_date), "%Y-%m-%d").date()
    #         date_start_format = start_date.strftime("%d/%m/%Y")
    #         final_start_date = datetime.datetime.strptime(
    #             str(date_start_format), "%d/%m/%Y").date()
    #         end_date = datetime.datetime.strptime(
    #             str(self.end_date), "%Y-%m-%d").date()
    #         date_end_format = end_date.strftime("%d/%m/%Y")
    #         final_end_date = datetime.datetime.strptime(
    #             str(date_end_format), "%d/%m/%Y").date()
    #         invoice = self.env['account.invoice'].search(
    #             [('type', '=', 'out_invoice')])
    #         print('invoice--------', invoice, self.start_date, self.end_date)
    #         payment = self.env['account.payment'].search([])
    #         print('---payments-----', payment)
    #         partner_list = []
    #         for invoices in invoice:
    #             if invoices.date_invoice:
    #                 invoices_date = datetime.datetime.strptime(
    #                     str(invoices.date_invoice), "%Y-%m-%d").date()
    #                 invoices_date_format = invoices_date.strftime("%d/%m/%Y")
    #                 final_invoices_date = datetime.datetime.strptime(
    #                     str(invoices_date_format), "%d/%m/%Y").date()
    #                 if final_start_date <= final_invoices_date <= final_end_date and not invoices.partner_id.email:
    #                     partner_list.append(invoices.partner_id.id)
    #         print('partners_list---invoice00000', partner_list)
    #         for payments in payment:
    #             if payments.payment_date:
    #                 payments_date = datetime.datetime.strptime(
    #                     str(payments.payment_date), "%Y-%m-%d").date()
    #                 payments_date_format = payments_date.strftime("%d/%m/%Y")
    #                 final_payment_date = datetime.datetime.strptime(
    #                     str(payments_date_format), "%d/%m/%Y").date()
    #                 if final_start_date <= final_payment_date <= final_end_date and not payments.partner_id.email:
    #                     partner_list.append(payments.partner_id.id)
    #         print('partner_list=------payment----', partner_list)
    #         self.partner_ids = [(6, 0, partner_list)]
    #         print('self.partner_li----', self.partner_ids)

    @api.multi
    def send_print_customer_statement(self):
        """For sending e-mail to multiple partners."""
        data = self.read([
            'start_date',
            'end_date',
        ])[0]
        partner_list = []
        email_partner_list = []
        if self.start_date > self.end_date:
            raise UserError(
                _("Start date should not be greater than end date"))
        else:
            template_id = self.env.ref(
                'nshore_customization.email_template_partner_statement')
            if template_id:
                # base_context = self.env.context
                partner_ids = self.env['res.partner'].sudo().search([('is_company', '=', True)])
                for partner in partner_ids:
                    template_id.write({'email_to': partner.email})
                    template_id.send_mail(partner.id, force_send=True)
                for email_partner in email_partner_list:
                    template_id.write({'email_to': email_partner.email})
                    template_id.send_mail(email_partner.id, force_send=True)
                if partner_list:
                    return self.env.ref(
                        'nshore_customization.custom_customer_statement'
                    ).report_action(
                        partner_list)

    @api.multi
    def print_customer_statement(self):
        """It creates pdf reports for particular partner."""
        data_dict = {}
        if self.start_date > self.end_date:
            raise UserError(
                _("Start date should not be greater than end date"))
        data = self.read([
            'start_date',
            'end_date'
        ])[0]
        partner_ids = self.env['res.partner'].sudo().search([
            ('is_company', '=', True)
        ]).ids
        data_dict.update({
            'partner_ids': partner_ids,
            'start_date': data['start_date'],
            'end_date': data['end_date']
        })
        return self.env.ref(
            'nshore_customization.custom_customer_statement'
        ).report_action(self, data_dict)
