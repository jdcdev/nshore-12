from datetime import datetime

from odoo import api, models


class ReportDailyMonthlyPayment(models.AbstractModel):
    _name = 'report.nshore_customization.report_daily_monthly_payment_1'

    _description = 'Report Daily Monthly Payment'

    def get_detail(self, payment_data, date_format):
        data = []
        if payment_data:
            payment_rec = self.env['account.payment'].search(
                [('payment_date', '>=', payment_data[0]),
                 ('payment_date', '<=', payment_data[1])])
            final_total = 0.0
            for payment in payment_rec:
                final_total += payment.amount
                payment_data = {}
                payment_data.update({
                    'date': payment.payment_date.strftime(date_format),
                    'payment_no': payment.name or payment.id,
                    'cust_no': payment.partner_id.parent_id.ref if payment.partner_id.parent_id else payment.partner_id.ref,
                    'cust_name': payment.partner_id.parent_id.name if payment.partner_id.parent_id else payment.partner_id.name,
                    'user': payment.sudo().create_uid.name,
                    'type': payment.journal_id.type,
                    'amount': payment.amount,
                    'final_total': final_total,
                })
                if payment_data:
                    data.append(payment_data)
        return data

    def get_detail_date(self, payment_data, date_format):
        data = []
        if payment_data:
            payment_rec = self.env['account.payment'].search(
                [('payment_date', '>=', payment_data[0]),
                 ('payment_date', '<=', payment_data[1])])
            for payment in payment_rec:
                data.append(payment.payment_date.strftime(date_format))
            data = list(set(data))
        data.sort(key = lambda date: datetime.strptime(date, '%m/%d/%Y'))
        return data

    def get_date_loop(self, payment_data):
        data = []
        if payment_data:
            payment_rec = self.env['account.payment'].search(
                [('payment_date', '>=', payment_data[0]),
                 ('payment_date', '<=', payment_data[1])])
            for payment in payment_rec:
                data.append(payment.payment_date)
            data = len(list(set(data)))
        return data

    def get_detail_total(self, payment_data):
        total = 0
        if payment_data:
            payment_rec = self.env['account.payment'].search(
                [('payment_date', '>=', payment_data[0]),
                 ('payment_date', '<=', payment_data[1])])
        for payment in payment_rec:
            total += payment.amount
        return total

    @api.model
    def _get_report_values(self, docids, data=None):
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format

        payment_data = []
        if data.get('form') and data['form'].get('from_date') and data['form'].get('to_date'):
            payment_data = [data['form'].get('from_date'), data['form'].get(
                'to_date')]
        lines_data = self.get_detail(payment_data, date_format)
        lines_data_date = self.get_detail_date(payment_data, date_format)
        get_detail_total = self.get_detail_total(payment_data)
        get_date_loop = self.get_date_loop(payment_data)
        return {
            'doc_model': 'account.payment',
            'data': data,
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
            'lines_data_date': lines_data_date,
            'get_detail_total': get_detail_total,
            'get_date_loop': get_date_loop,
            'currency_id': self.env.user.company_id.currency_id
        }
