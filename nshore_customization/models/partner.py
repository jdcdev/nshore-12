# See LICENSE file for full copyright and licensing details.
import base64
import datetime
from calendar import monthrange
from odoo import api, fields, models
from odoo.addons.queue_job.job import job


class ResPartner(models.Model):
    """Class inherit to add some fields and function."""

    _inherit = 'res.partner'

    over_credit = fields.Boolean('Allow Over Credit?', default=True)
    allow_supervisor = fields.Boolean('Allow Supervisor', default=False)
    fax = fields.Char(string="Fax")
    invoice_start_date = fields.Date('Invoice Start Date')
    invoice_end_date = fields.Date('Invoice Start Date')

    @api.multi
    def name_get(self):
        """Function call to get name in title."""
        res = []
        for partner in self:
            name = partner._get_name()
            res.append((partner.id, name.replace('_', ' ').title()))
        return res

    def send_customer_statement(self):
        """Function call for job."""
        self.with_delay()._send_customer_statement()

    @job
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
        invoices = self.env['account.invoice'].search([
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('state', 'not in', ['draft', 'cancel'])])
        payments = self.env['account.payment'].search([
            ('partner_type', '=', 'customer'),
            ('state', 'in', ['posted'])])
        partner_obj = self.env['res.partner']
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
                pay_date = datetime.datetime.strptime(
                    str(payment.payment_date), "%Y-%m-%d")
                pay_date_format = pay_date.strftime("%d/%m/%Y")
                final_pay_date = datetime.datetime.strptime(
                    str(pay_date_format), "%d/%m/%Y")
                if final_start_date <= final_pay_date <= final_end_date:
                    partner_list.append(payment.partner_id.id)
        if partner_list:
            partner_list = list(set(partner_list))
            template_id = self.env.ref(
                'nshore_customization.email_template_partner_statement')
            ctx = {
                'start_date': final_start_date,
                'end_date': final_end_date
            }
            partners = partner_obj.browse(partner_list)
            for partner in partners.filtered(lambda l: l.email):
                partner.sudo().write({
                    'invoice_start_date': final_start_date,
                    'invoice_end_date': final_end_date
                })
                if partner.email:
                    template_id.write({'email_to': partner.email})
                    template_id.with_context(ctx).send_mail(partner.id,
                                                            force_send=False)
            cst_stmt_pdf = self.env.ref(
                'nshore_customization.custom_customer_statement'
            ).with_context(ctx).render_qweb_pdf(partners.ids)[0]
            cst_stmt_pdf_encode = base64.b64encode(cst_stmt_pdf)
            pdf_name = 'Customer Statement Report: %s.pdf' % today
            self.env['ir.attachment'].sudo().create({
                'name': pdf_name,
                'datas_fname': pdf_name,
                'datas': cst_stmt_pdf_encode,
                'res_model': log._name,
                'res_id': log.id,
                'type': 'binary',
                'mimetype': 'application/pdf'})
