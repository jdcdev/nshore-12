from odoo import api, models, fields
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class CustomerStatementReport(models.AbstractModel):
    """Class call to add statement report."""

    _name = 'report.nshore_customization.report_customer_statement_1'

    _description = 'Report Customer Statement'

    def get_detail_date(self, data, date_format):
        """Function call to get all date value."""
        data_date = []
        partner_ids = self.env['res.partner'].browse(data['partner_ids'])
        start_date = data['start_date']
        end_date = data['end_date']
        if data:
            for partner in partner_ids:
                invoice_rec = self.env['account.invoice'].search(
                    [('partner_id', '=', partner.id),
                        ('type', 'in', ['out_invoice', 'out_refund']),
                        ('state', 'not in', ['draft', 'cancel']),
                        ('date_invoice', '>=', start_date),
                        ('date_invoice', '<=', end_date)])
                payment_rec = self.env['account.payment'].search([
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ['posted']),
                    ('payment_date', '>=', start_date),
                    ('payment_date', '<=', end_date)])
                account_move = self.env['account.move.line'].search(
                    [('journal_id', '=', 4), ('partner_id', '=', partner.id),
                        ('move_id.state', '=', 'posted')])
                for move in account_move:
                    data_date.append(move.date.strftime(
                        date_format))
                    data_date = list(set(data_date))
                for pay in payment_rec:
                    data_date.append(pay.payment_date.strftime(
                        date_format))
                    data_date = list(set(data_date))
                for invoice in invoice_rec:
                    data_date.append(invoice.date_invoice.strftime(
                        date_format))
                    data_date = list(set(data_date))
        data_date.sort(key=lambda date: datetime.strptime(date, '%m/%d/%Y'))
        return data_date

    def get_invoice_details(self, data, date_format):
        """Function call to get invoice."""
        partner_ids = self.env['res.partner'].browse(data['partner_ids'])
        partner_dict = {}
        start_date = data['start_date']
        end_date = data['end_date']
        # get all open invoice and credit not for opening balance.
        invoice_obj = self.env['account.invoice']
        payment_obj = self.env['account.payment']
        for partner in partner_ids:
            # Open Invoices
            open_invoices = invoice_obj.search([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'in', ['paid', 'open']),
                ('date_invoice', '<', start_date),
            ])
            amount_inv = amount_crnote = total_open_bal_invoice = open_payment = 0.0
            for open_invoice in open_invoices:
                if type(start_date) and type(end_date) is str:
                    start_date_wiz = datetime.strptime(start_date, '%Y-%m-%d').date()
                if isinstance(start_date, datetime):
                    start_date_wiz = start_date.date()
                if not isinstance(start_date, datetime) and not type(start_date) is str:
                    start_date_wiz = start_date
                if open_invoice.type == 'out_invoice':
                    if open_invoice.state == 'paid':
                        if not open_invoice.payment_ids:
                            amount_inv += open_invoice.amount_total
                        for payment in open_invoice.payment_ids.filtered(
                                lambda p: p.state == 'posted'):
                            if payment.payment_date < start_date_wiz:
                                amount_inv += (
                                    open_invoice.amount_total - payment.amount)
                            else:
                                amount_inv += open_invoice.amount_total
                    if open_invoice.state == 'open':
                        amount_inv += open_invoice.amount_total
                if open_invoice.type == 'out_refund':
                    if open_invoice.state == 'paid':
                        if not open_invoice.payment_ids:
                            amount_crnote += open_invoice.amount_total
                        for payment in open_invoice.payment_ids.filtered(
                                lambda p: p.state == 'posted'):
                            if payment.payment_date < start_date_wiz:
                                amount_crnote += (
                                    open_invoice.amount_total - payment.amount)
                            else:
                                amount_crnote += open_invoice.amount_total
                    if open_invoice.state == 'open':
                        amount_crnote += open_invoice.amount_total
            total_open_bal_invoice = amount_inv - amount_crnote
            for pay in payment_obj.search([
                    '|',
                    ('partner_id', '=', partner.id),
                    ('partner_id.parent_id', '=', partner.id),
                    ('state', '=', 'posted'),
                    ('payment_date', '<', start_date),
                    ('invoice_ids', '=', False)]):
                if pay.payment_type == 'inbound':
                    open_pay_amount = - 1 * pay.amount
                if pay.payment_type == 'outbound':
                    open_pay_amount = pay.amount
                open_payment += open_pay_amount or 0.0
            # Get all invoices and credit notes between selected dates.
            total_credit_note_amount = total_invoice_amount = total_pay = 0.0
            for invoice in invoice_obj.search([
                    ('partner_id', '=', partner.id),
                    ('type', 'in', ['out_invoice', 'out_refund']),
                    ('state', 'not in', ['draft', 'cancel']),
                    ('date_invoice', '>=', start_date),
                    ('date_invoice', '<=', end_date)],
                    order='date_invoice,id asc'):
                if invoice.type == 'out_invoice':
                    amount_total = invoice.amount_total
                    total_invoice_amount += invoice.amount_total
                elif invoice.type == 'out_refund':
                    amount_total = -1 * invoice.amount_total
                    total_credit_note_amount += (-1 * invoice.amount_total)
                invoice_num = ''
                if len(invoice.number) != 6:
                    invoice_num = invoice.number[-6:]
                else:
                    invoice_num = invoice.number
                vals_dict = {
                    'date_invoice': invoice.date_invoice.strftime(
                        date_format),
                    'name': invoice_num,
                    'amount_total': amount_total,
                    'residual': invoice.residual,
                    'partner_shipping_id': invoice.partner_shipping_id,
                    'due_date': invoice.date_due.strftime(
                        date_format),
                    'type': invoice.type
                }
                if partner not in partner_dict.keys():
                    partner_dict.update({
                        partner: {
                            'invoice_line': [vals_dict],
                        }
                    })
                else:
                    partner_dict[partner]['invoice_line'].append(vals_dict)
            # Get opening balance from journal(Miscellaneous Operations (USD))
            account_move = self.env['account.move.line'].search(
                [('journal_id', '=', 4), ('partner_id', '=', partner.id),
                    ('move_id.state', '=', 'posted')])
            open_cr_amount = open_dr_amount = totalmove = 0.0
            move_dict = {}
            move_records = []
            # for move in account_move:
            if type(start_date) and type(end_date) is str:
                start_date_wiz = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_wiz = datetime.strptime(end_date, '%Y-%m-%d').date()
            if isinstance(start_date, datetime):
                start_date_wiz = start_date.date()
                end_date_wiz = end_date.date()
            if not isinstance(start_date, datetime) and not type(start_date) is str:
                start_date_wiz = start_date
                end_date_wiz = end_date
            for m_lines in account_move.filtered(
                    lambda l: l.account_id.code in ['1200', '2000'] and l.date < start_date_wiz):
                if m_lines.credit != 0.0:
                    open_cr_amount += -1 * m_lines.credit
                if m_lines.debit != 0.0:
                    open_dr_amount += m_lines.debit
            # append Misc entries on partner dict.
            for move_lines in account_move.filtered(
                    lambda l: l.account_id.code in ['1200', '2000'] and l.date >= start_date_wiz and l.date <= end_date_wiz):
                if move_lines.credit != 0.0:
                    move_amount = -1 * move_lines.credit
                if move_lines.debit != 0.0:
                    move_amount = move_lines.debit
                totalmove += move_amount
                move_dict = {
                    'move_name': move_lines.move_id.name[-4:],
                    'move_date': move_lines.date.strftime(
                        date_format),
                    'move_amount': move_amount}
                if partner not in partner_dict.keys():
                    partner_dict.update({
                        partner: {'move_line': [move_dict]}})
                else:
                    move_records.append(move_dict)
            # Append Payments record on Partner dict
            if move_records:
                partner_dict[partner]['move_line'] = move_records
            total_open_move_amount = (
                open_dr_amount + open_cr_amount)
            # Append Opening Balance in Partner Dict
            opening_balance = (
                total_open_bal_invoice + total_open_move_amount + open_payment)
            if opening_balance:
                if partner not in partner_dict.keys():
                    partner_dict.update({
                        partner: {
                            'open_inv_amount': opening_balance,
                        }
                    })
                else:
                    partner_dict[partner][
                        'open_inv_amount'] = opening_balance
            # Get all between payments records
            payment_records = []
            for pay in payment_obj.search([
                '|',
                ('partner_id', '=', partner.id),
                ('partner_id.parent_id', '=', partner.id),
                ('state', 'in', ['posted']),
                ('payment_date', '>=', start_date),
                ('payment_date', '<=', end_date)],
                    order='payment_date,id asc'):
                if pay.payment_type == 'inbound':
                    pay_amount = - 1 * pay.amount
                if pay.payment_type == 'outbound':
                    pay_amount = pay.amount
                total_pay += pay_amount
                pay_dict = {
                    'pay_name': pay.name[-4:],
                    'pay_date': pay.payment_date.strftime(
                        date_format),
                    'pay_amount': pay_amount,
                }
                if partner not in partner_dict.keys():
                    partner_dict.update({
                        partner: {'payment_line': [pay_dict]}})
                else:
                    payment_records.append(pay_dict)
            # Append Payments record on Partner dict
            if payment_records:
                partner_dict[partner]['payment_line'] = payment_records
            if partner not in partner_dict.keys():
                partner_dict.update({
                    partner: {'partner_shipping_id': partner}
                })
            if partner in partner_dict.keys() and not any(
                    [x for x in partner_dict[partner].get(
                        'invoice_line', []) if 'partner_shipping_id' in x.keys()]):
                partner_dict[partner].update({'partner_shipping_id': partner})
            on_account_cr_note = ([
                ('partner_id', '=', partner.id),
                ('type', '=', 'out_refund'),
                ('state', '=', 'open'),
                ('date_invoice', '<', start_date)])
            on_account = sum(
                [invoice.amount_untaxed for invoice in invoice_obj.search(
                    on_account_cr_note)])
            results, total, amls = self.env[
                'report.account.report_agedpartnerbalance'].with_context(
                include_nullified_amount=True)._get_partner_move_lines(
                ['receivable'], start_date, 'posted', 30)
            for rec in results:
                if rec['partner_id'] == partner.id:
                    cust_dict = {
                        'current_amount': rec['direction'],
                        'between_30days': rec['4'],
                        'between_60days': rec['3'],
                        'between_90days': rec['2'],
                        'plus_90days': rec['1'],
                        'on_account': on_account
                    }
                    partner_dict[partner].update(cust_dict)
        return partner_dict

    @api.model
    def _get_report_values(self, docids, data=None):
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        if not data.get('partner_ids'):
            data.update({'partner_ids': docids})
        data.update(self._context)
        partner_ids = data.get('partner_ids')
        lines_data = self.get_invoice_details(data, date_format)
        get_detail_date = self.get_detail_date(data, date_format)
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(partner_ids),
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
            'date_data': get_detail_date
        }
