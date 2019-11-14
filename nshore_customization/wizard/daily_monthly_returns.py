# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DailyMonthlyReturns(models.TransientModel):
    _name = "daily.monthly.returns"

    _description = 'Daily Monthly Returns'

    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')

    @api.multi
    def print_report(self):
        data = self.read()[0]
        res = {'ids': [],
               'model': 'account.invoice',
               'form': data
               }
        return self.env.ref(
            'nshore_customization.daily_monthly_returns').report_action(
            [], data=res)
