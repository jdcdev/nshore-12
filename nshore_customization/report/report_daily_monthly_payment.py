from datetime import datetime

from odoo import api, models


class ReportDailyMonthlyPayment(models.AbstractModel):
    _name = 'report.nshore_customization.report_daily_monthly_payment'

    _description = 'Report Daily Monthly Payment'

    def get_detail(self, payment_data, date_format):
        data = []
        if payment_data:
            payment_rec = self.env['account.payment'].search(
                [('payment_date', '>=', payment_data[0]),
                 ('payment_date', '<=', payment_data[1])])
            for payment in payment_rec:
                payment_data = {}
                payment_data.update({
                    'date': datetime.strptime(
                        payment.payment_date, '%Y-%m-%d').strftime(
                        date_format),
                    'payment_no': payment.name or payment.id,
                    'cust_no': payment.partner_id.id,
                    'cust_name': payment.partner_id.name,
                    'user': payment.sudo().create_uid.name,
                    'type': payment.journal_id.type,
                    'amount': payment.amount,
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
                data.append(datetime.strptime(
                    payment.payment_date, '%Y-%m-%d').strftime(
                    date_format))
            data = list(set(data))
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

    def get_detail_total(self):
        total = 0
        payment_rec = self.env['account.payment'].search([])
        for payment in payment_rec:
            total += payment.amount
        return total

    @api.model
    def get_report_values(self, docids, data=None):
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        register_ids = self.env.context.get('active_ids', [])
        payment = self.env['account.payment'].browse(register_ids)
        payment_data = []
        if data['form'].get('from_date') and data['form'].get('to_date'):
            payment_data = [data['form'].get('from_date'), data['form'].get(
                'to_date')]
        lines_data = self.get_detail(payment_data, date_format)
        lines_data_date = self.get_detail_date(payment_data, date_format)
        get_detail_total = self.get_detail_total()
        get_date_loop = self.get_date_loop(payment_data)
        return {
            'doc_ids': register_ids,
            'doc_model': 'account.payment',
            'data': data,
            'docs': payment,
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
            'lines_data_date': lines_data_date,
            'get_detail_total': get_detail_total,
            'get_date_loop': get_date_loop,
        }
