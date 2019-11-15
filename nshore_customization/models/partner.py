# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    over_credit = fields.Boolean('Allow Over Credit?', default=True)
    allow_supervisor = fields.Boolean('Allow Supervisor', default=False)
    fax = fields.Char(string="Fax")
    invoice_start_date = fields.Date('Invoice Start Date')
    invoice_end_date = fields.Date('Invoice Start Date')

    @api.model
    def _send_customer_statement(self):
        final_start_date = datetime.datetime.today() + relativedelta(
            months=-1)
        final_end_date = datetime.datetime.today()
        invoice = self.env['account.invoice'].search(
            [('type', '=', 'out_invoice')])
        payment = self.env['account.payment'].search([])
        partner_list = []
        for invoices in invoice:
            if invoices.date_invoice:
                invoices_date = datetime.datetime.strptime(
                    str(invoices.date_invoice), "%Y-%m-%d")
                invoices_date_format = invoices_date.strftime("%d/%m/%Y")
                final_invoices_date = datetime.datetime.strptime(
                    str(invoices_date_format), "%d/%m/%Y")
                if final_start_date <= final_invoices_date <= final_end_date:
                    partner_list.append(invoices.partner_id.id)
        for payments in payment:
            if payments.payment_date:
                payments_date = datetime.datetime.strptime(
                    str(payments.payment_date), "%Y-%m-%d")
                payments_date_format = payments_date.strftime("%d/%m/%Y")
                final_payment_date = datetime.datetime.strptime(
                    str(payments_date_format), "%d/%m/%Y")
                if final_start_date <= final_payment_date <= final_end_date:
                    partner_list.append(payments.partner_id.id)
        if partner_list:
            partner_list = list(set(partner_list))
            template_id = self.env.ref(
                'nshore_customization.email_template_partner_statement')
            for partner in self.env['res.partner'].browse(partner_list):
                partner.sudo().write({
                    'invoice_start_date': final_start_date,
                    'invoice_end_date': final_end_date
                })
                if partner.email:
                    template_id.write({'email_to': partner.email})
                    template_id.send_mail(partner.id, force_send=True)
