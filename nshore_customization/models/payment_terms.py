# -*- coding: utf-8 -*-
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import datetime


class AccountPaymentTermLine(models.Model):
    """Class inherited to add fields."""

    _inherit = "account.payment.term.line"
    _description = "Payment Terms Line"

    option = fields.Selection([
        ('day_after_invoice_date', "day(s) after the invoice date"),
        ('after_invoice_month', "day(s) after the end of the invoice month"),
        ('day_following_month', "of the following month"),
        ('day_current_month', "of the current month"),
        ('fix_month', "of Month")],
        default='day_after_invoice_date', required=True, string='Options')
    months = fields.Integer(string='Number of Months')


class AccountPaymentTerm(models.Model):
    """Class Inherited to override function."""

    _inherit = "account.payment.term"

    @api.one
    def compute(self, value, date_ref=False):
        """Function override to add month functinality on line."""
        date_ref = date_ref or fields.Date.today()
        amount = value
        sign = value < 0 and -1 or 1
        result = []
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(
                self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value == 'balance':
                amt = currency.round(amount)
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                    if line.day_of_the_month > 0:
                        months_delta = (
                            line.day_of_the_month < next_date.day) and 1 or 0
                        next_date += relativedelta(
                            day=line.day_of_the_month, months=months_delta)
                elif line.option == 'after_invoice_month':
                    next_first_date = next_date + relativedelta(
                        day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(
                        days=line.days - 1)
                elif line.option == 'day_following_month':
                    next_date += relativedelta(day=line.days, months=1)
                elif line.option == 'day_current_month':
                    next_date += relativedelta(day=line.days, months=0)
                elif line.option == 'fix_month':
                    current_date = fields.Date.from_string(date_ref)
                    if line.months > 0:
                        day = str(line.days)
                        month = str(line.months)
                        year = current_date.year
                        if current_date.month >= line.months:
                            if current_date.day >= line.days:
                                final_year = year + 1
                                next_day_date = str(
                                    final_year) + '-' + month + '-' + day
                                next_date = datetime.strptime(
                                    next_day_date, '%Y-%m-%d').date()
                            elif current_date.day <= line.days:
                                next_day_date = str(
                                    current_date.year) + '-' + month + '-' + day
                                next_date = datetime.strptime(
                                    next_day_date, '%Y-%m-%d').date()
                        else:
                            next_day_date = str(
                                current_date.year) + '-' + month + '-' + day
                            next_date = datetime.strptime(
                                next_day_date, '%Y-%m-%d').date()
                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt
        amount = sum(amt for _, amt in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))
        return result
