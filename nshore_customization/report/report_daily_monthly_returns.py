from datetime import datetime

from odoo import api, models


class ReportDailyMonthlyReturns(models.AbstractModel):
    _name = 'report.nshore_customization.report_daily_monthly_returns'

    def get_detail(self, invoice_data, date_format):
        data = []
        if invoice_data:
            invoice_rec = self.env['account.invoice'].search(
                [('date_invoice', '>=', invoice_data[0]),
                 ('date_invoice', '<=', invoice_data[1]),
                 ('type', 'in', ['out_refund', 'in_refund'])])
            for invoice in invoice_rec:
                invoice_data = {}
                invoice_amount = discount_amount = 0
                for invoice_line in invoice.invoice_line_ids:
                    invoice_amount +=\
                        invoice_line.price_unit * invoice_line.quantity
                    discount_amount += invoice_line.discount
                invoice_data.update({
                    'date': datetime.strptime(
                        invoice.date_invoice, '%Y-%m-%d').strftime(
                        date_format),
                    'number': invoice.number or invoice.id,
                    'cust_no': invoice.partner_id.id,
                    'customer': invoice.partner_id.name,
                    'user': invoice.user_id.name,
                    'amount': invoice_amount,
                    'discount': discount_amount,
                    'tax': invoice.amount_tax,
                    'total': invoice.amount_total,
                })
                if invoice_data:
                    data.append(invoice_data)
        return data

    def get_detail_date(self, invoice_data, date_format):
        data = []
        if invoice_data:
            invoice_rec = self.env['account.invoice'].search(
                [('date_invoice', '>=', invoice_data[0]),
                 ('date_invoice', '<=', invoice_data[1]),
                 ('type', 'in', ['out_refund', 'in_refund'])
                 ])
            for invoice in invoice_rec:
                data.append(datetime.strptime(
                    invoice.date_invoice, '%Y-%m-%d').strftime(
                    date_format))
            data = list(set(data))
        return data

    def get_detail_total_loop(self, invoice_data):
        data = []
        if invoice_data:
            invoice_rec = self.env['account.invoice'].search(
                [('date_invoice', '>=', invoice_data[0]),
                 ('date_invoice', '<=', invoice_data[1]),
                 ('type', 'in', ['out_refund', 'in_refund'])
                 ])
            for invoice in invoice_rec:
                data.append(invoice.date_invoice)
            data = len(list(set(data)))
        return data

    def get_total_detail(self):
        data = []
        invoice_rec_total = self.env['account.invoice'].search([
            ('type', 'in', ['out_refund', 'in_refund'])])
        invoice_total_amount = discount_total_amount = amount_tax_total =\
            total = 0
        for inv in invoice_rec_total:
            amount_tax_total += inv.amount_tax
            total += inv.amount_total
            for inv_line in inv.invoice_line_ids:
                invoice_total_amount +=\
                    inv_line.price_unit * inv_line.quantity
                discount_total_amount += inv_line.discount
        data.append({'invoice_total_amount': invoice_total_amount,
                     'discount_total_amount': discount_total_amount,
                     'amount_tax_total': amount_tax_total,
                     'total': total})
        return data

    @api.model
    def get_report_values(self, docids, data=None):
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        register_ids = self.env.context.get('active_ids', [])
        invoice = self.env['account.invoice'].browse(register_ids)
        invoice_data = []
        if data['form'].get('from_date') and data['form'].get('to_date'):
            invoice_data = [data['form'].get('from_date'), data['form'].get(
                'to_date')]
        lines_data = self.get_detail(invoice_data, date_format)
        lines_total_data = self.get_total_detail()
        get_detail_date = self.get_detail_date(invoice_data, date_format)
        get_detail_total_loop = self.get_detail_total_loop(invoice_data)
        return {
            'doc_ids': register_ids,
            'doc_model': 'account.invoice',
            'data': data,
            'docs': invoice,
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
            'lines_total_data': lines_total_data,
            'get_detail_date': get_detail_date,
            'get_detail_total_loop': get_detail_total_loop,
        }
