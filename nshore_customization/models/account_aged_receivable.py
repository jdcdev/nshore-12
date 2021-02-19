# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date

class report_account_aged_receivable(models.AbstractModel):
    _inherit = "account.aged.partner"
    _description = "Aged Partner Balances"

    def _get_columns_name(self, options):
        # Function call to add column when account.aged.receivable
        columns = [{}]
        columns += [
            {'name': v, 'class': 'number', 'style': 'white-space:nowrap;'}
            for v in [_("JRNL"), _("Last Payment Date"), _("Last Payment Amount"), _("Account"), _("Reference"), _("Not due on: %s") % format_date(self.env, options['date']['date']),
                      _("1 - 30"), _("31 - 60"), _("61 - 90"), _("91 - 120"), _("Older"), _("Total")]
        ]
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        # Function call to add last payment date and amount in aged rece report.
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
        # Payment line total
        payment_lines = self.env['account.partial.reconcile']
        all_payment_by_partner = {}
        partners_amount = {}
        final_payment_date = {}
        total_payment_amount_final = total_payment_amount = 0.0
        for values in results:
            # Payment amount total, and total by partner
            partners_amount[(values['partner_id'])] = 0.0
            final_payment_date[(values['partner_id'])] = ''
            all_payment_list = []
            for move_lines in amls[values['partner_id']]:
                m_line = move_lines.get('line')
                if m_line.journal_id.code in ['INV', 'BILL', 'CSH1', 'CC', 'CHK', 'BNK1']:
                    payment_line = payment_lines.search(['|', ('debit_move_id', '=', m_line.id), ('credit_move_id', '=', m_line.id)], order="id desc", limit=1)
                    # Added condition on Journal for moves
                    total_payment_amount += payment_line.amount if m_line.journal_id.code in ['INV', 'BILL', 'CSH1', 'CC', 'CHK', 'BNK1'] else 0.0
                    total_payment_amount_final = ("{0:.2f}".format(total_payment_amount))
                    # Get all payment id by partner
                    all_payment_list.append(int(payment_line))
                    all_payment_by_partner[(values['partner_id'])] = all_payment_list
                    res = {}
                    # Get Latest payment amount and date from moves(most recent)
                    for key in all_payment_by_partner:
                        res[key] = sorted(all_payment_by_partner[key], reverse=True)[0]
                        payment_line_sorted = payment_lines.browse(res[key])
                        final_payment_date[(values['partner_id'])] = payment_line_sorted.max_date
                        partners_amount[(values['partner_id'])] = payment_line_sorted.amount
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            # Add total by partner in vals
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] * 1 + [{'name': final_payment_date[(values['partner_id'])]}] + [{'name': partners_amount[(values['partner_id'])]}] + [{'name': ''}] * 2 + [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'],
                                                                                                 values['3'], values['2'],
                                                                                                 values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    # Get last payment amount and date for invoice by partner
                    payment_line = payment_lines.search(['|', ('debit_move_id', '=', aml.id), ('credit_move_id', '=', aml.id)], order="id desc", limit=1)
                    payment_date = payment_line.max_date if payment_line.max_date else ' '
                    # Added condition on Journal for moves
                    payment_date = payment_date if aml.journal_id.code in ['INV', 'BILL', 'CSH1', 'CC', 'CHK', 'BNK1'] else ' '
                    payment_amount = payment_line.amount if aml.journal_id.code in ['INV', 'BILL', 'CSH1', 'CC', 'CHK', 'BNK1'] else 0.0
                    caret_type = 'account.move'
                    if aml.invoice_id:
                        caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    # added last payment amount and date in move lines(unfold)
                    vals = {
                        'id': aml.id,
                        'name': line_date,
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [aml.journal_id.code, str(payment_date), payment_amount, aml.account_id.code, self._format_aml_name(aml)]] +\
                                   [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount']) or '' for i in range(7)]],
                        'action_context': aml.get_action_context(),
                    }
                    lines.append(vals)
        if total and not line_id:
            # Add fianl total of payment amount
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 2 + [{'name': total_payment_amount_final}] + [{'name': ''}] * 2 + [{'name': self.format_value(sign * v)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines