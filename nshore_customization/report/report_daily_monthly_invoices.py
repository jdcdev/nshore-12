from datetime import datetime
from odoo import api, models


class ReportDailyMonthlyInvoices(models.AbstractModel):
    """Class added for DM invoice report."""

    _name = 'report.nshore_customization.report_daily_monthly_invoices'

    _description = 'Report Daily Monthly Invoices'

    def get_detail(self, invoice_data, date_format):
        """Function call to get invoice data."""
        data = []
        if invoice_data:
            invoice_rec = self.env['account.invoice'].search(
                [('date_invoice', '>=', invoice_data[0]),
                 ('date_invoice', '<=', invoice_data[1]),
                 ('type', 'in', ['out_invoice', 'out_refund']),
                 ('state', 'in', ['paid', 'open'])])
            for invoice in invoice_rec:
                invoice_num = ''
                if invoice.number:
                    invoice_num = str(invoice.number).replace('INV/', '')
                invoice_data = {}
                invoice_amount = discount_amount = 0
                invoice_total = 0
                for invoice_line in invoice.invoice_line_ids:
                    invoice_amount +=\
                        invoice_line.price_unit * invoice_line.quantity
                    discount_amount += invoice_line.discount
                if invoice.type == 'out_refund':
                    invoice_total = -1 * invoice.amount_total
                    amount_tax = -1 * invoice.amount_tax
                    discount_amount = -1 * discount_amount
                    invoice_amount = -1 * invoice_amount
                elif invoice.type == 'out_invoice':
                    invoice_total = invoice.amount_total
                    amount_tax = invoice.amount_tax
                    discount_amount = discount_amount
                    invoice_amount = invoice_amount
                invoice_data.update({
                    'date': invoice.date_invoice.strftime(
                        date_format),
                    'number': invoice_num or invoice.id,
                    'cust_no': invoice.partner_id.parent_id.ref if invoice.partner_id.parent_id else invoice.partner_id.ref,
                    'customer': invoice.partner_id.parent_id.name if invoice.partner_id.parent_id else invoice.partner_id.name,
                    'user': invoice.user_id.name,
                    'amount': invoice_amount,
                    'discount': discount_amount,
                    'tax': amount_tax,
                    'total': invoice_total,
                })
                if invoice_data:
                    data.append(invoice_data)
        return data

    def get_total_detail(self, invoice_data):
        """Function call o get total details."""
        data = []
        invoice_rec_total = self.env['account.invoice'].search(
            [('date_invoice', '>=', invoice_data[0]),
                ('date_invoice', '<=', invoice_data[1]),
                ('state', 'in', ['paid', 'open'])])
        invoice_total_amount = discount_total_amount = amount_tax_total =\
            total = 0
        for inv in invoice_rec_total:
            if inv.type == 'out_refund':
                amount_tax_total += (-1 * inv.amount_tax)
                total += (-1 * inv.amount_total)
                for inv_line in inv.invoice_line_ids:
                    invoice_total_amount += (-1 * (
                        inv_line.price_unit * inv_line.quantity))
                    discount_total_amount += (-1 * inv_line.discount)
            elif inv.type == 'out_invoice':
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

    def get_detail_date(self, invoice_data, date_format):
        """Function call to get date details."""
        data = []
        if invoice_data:
            invoice_rec = self.env['account.invoice'].search(
                [('date_invoice', '>=', invoice_data[0]),
                 ('date_invoice', '<=', invoice_data[1]),
                 ('state', 'in', ['paid', 'open'])])
            for invoice in invoice_rec:
                data.append(invoice.date_invoice.strftime(date_format))
            data = list(set(data))
        data.sort(key=lambda date: datetime.strptime(date, '%m/%d/%Y'))
        return data

    def get_date_loop(self, invoice_data):
        """Function call to get loop dates."""
        data = []
        if invoice_data:
            invoice_rec = self.env['account.invoice'].search(
                [('date_invoice', '>=', invoice_data[0]),
                 ('date_invoice', '<=', invoice_data[1]),
                 ('state', 'in', ['paid', 'open'])])
            for invoice in invoice_rec:
                data.append(invoice.date_invoice)
            data = len(list(set(data)))
        return data

    @api.model
    def _get_report_values(self, docids, data=None):
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        register_ids = self.env.context.get('active_ids', [])
        invoice_data = []
        if data['form'].get('from_date') and data['form'].get('to_date'):
            invoice_data = [data['form'].get('from_date'), data['form'].get(
                'to_date')]
        lines_data = self.get_detail(invoice_data, date_format)
        lines_total_data = self.get_total_detail(invoice_data)
        get_detail_date = self.get_detail_date(invoice_data, date_format)
        get_detail_total_loop = self.get_date_loop(invoice_data)
        vals = {
            'doc_ids': register_ids,
            'doc_model': 'account.invoice',
            'data': data,
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
            'get_detail_date': get_detail_date,
            'lines_total_data': lines_total_data,
            'get_detail_total_loop': get_detail_total_loop,
            'currency_id': self.env.user.company_id.currency_id
        }
        return vals
