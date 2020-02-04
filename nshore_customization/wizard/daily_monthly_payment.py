# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DailyMonthlyPayment(models.TransientModel):
    _name = "daily.monthly.payment"

    _description = 'Daily Monthly Payement'

    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')

    @api.multi
    def print_report(self):
        data = self.read()[0]
        res = {'ids': [],
               'model': 'account.payment',
               'form': data
               }
        return self.env.ref(
            'nshore_customization.daily_monthly_payment').report_action(
            [], data=res)
