from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models


class payroll_advice_report(models.AbstractModel):
    _name = 'report.nshore_customization.report_customer_statement'

    _description = 'Report Customer Statement'

    def get_invoice_details(self, docids, date_format):
        partner = self.env['res.partner'].browse(docids)
        data = []
        if partner.invoice_start_date:
            invoice_start_date = partner.invoice_start_date
        else:
            invoice_start_date = datetime.today() + relativedelta(months=-1)
        if partner.invoice_end_date:
            invoice_end_date = partner.invoice_end_date
        else:
            invoice_end_date = datetime.today()
        for invoice in self.env['account.invoice'].search([
                ('partner_id', '=', partner.id),
                ('state', '!=', 'draft'),
                ('date_invoice', '>=', invoice_start_date),
                ('date_invoice', '<=', invoice_end_date)]):
            data.append({'date_invoice':
                         datetime.strptime(
                             invoice.date_invoice, '%Y-%m-%d').strftime(
                             date_format),
                         'name': invoice.name,
                         'amount_total': invoice.amount_total,
                         'residual': invoice.residual})
        return data

    @api.model
    def get_report_values(self, docids, data=None):
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        lines_data = self.get_invoice_details(docids, date_format)
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(docids),
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
        }
