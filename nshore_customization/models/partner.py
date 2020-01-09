# See LICENSE file for full copyright and licensing details.

import base64
import datetime
from calendar import monthrange

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    over_credit = fields.Boolean('Allow Over Credit?', default=True)
    allow_supervisor = fields.Boolean('Allow Supervisor', default=False)
    fax = fields.Char(string="Fax")
    invoice_start_date = fields.Date('Invoice Start Date')
    invoice_end_date = fields.Date('Invoice Start Date')

    @api.model
    def _send_customer_statement(self):
        today = datetime.datetime.today()
        if today.month == 1:
            final_start_date = today.replace(day=1, month=12,
                                             year=today.year - 1)
            final_end_date = final_start_date.replace(day=31)
        else:
            final_start_date = today.replace(day=1, month=today.month - 1)
            final_end_date = final_start_date.replace(
                day=monthrange(final_start_date.year,
                               final_start_date.month)[1])
        invoices = self.env['account.invoice'].search(
            [('type', '=', 'out_invoice')])
        payments = self.env['account.payment'].search([])
        partner_obj = self.env['res.partner']
        attachment = self.env['ir.attachment']
        log = self.env['customer.statement.unmail']
        partner_list = []
        for invoice in invoices:
            if invoice.date_invoice:
                invoice_date = datetime.datetime.strptime(
                    str(invoice.date_invoice), "%Y-%m-%d")
                invoices_date_format = invoice_date.strftime("%d/%m/%Y")
                final_invoices_date = datetime.datetime.strptime(
                    str(invoices_date_format), "%d/%m/%Y")
                if final_start_date <= final_invoices_date <= final_end_date:
                    partner_list.append(invoice.partner_id.id)
        for payment in payments:
            if payment.payment_date:
                payment_date = datetime.datetime.strptime(
                    str(payment.payment_date), "%Y-%m-%d")
                payment_date_format = payment_date.strftime("%d/%m/%Y")
                final_payment_date = datetime.datetime.strptime(
                    str(payment_date_format), "%d/%m/%Y")
                if final_start_date <= final_payment_date <= final_end_date:
                    partner_list.append(payment.partner_id.id)
        if partner_list:
            partner_list = list(set(partner_list))
            template_id = self.env.ref(
                'nshore_customization.email_template_partner_statement')
            for partner in partner_obj.browse(partner_list):
                partner.sudo().write({
                    'invoice_start_date': final_start_date,
                    'invoice_end_date': final_end_date
                })
                if partner.email:
                    template_id.write({'email_to': partner.email})
                    template_id.with_context({
                        'start_date': final_start_date,
                        'end_date': final_end_date
                    }).send_mail(partner.id, force_send=True)
