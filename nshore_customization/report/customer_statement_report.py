from datetime import datetime
from odoo import api, models, fields
from dateutil.relativedelta import relativedelta


class CustomerStatementReport(models.AbstractModel):
    """Class call to add statement report."""

    _name = 'report.nshore_customization.report_customer_statement_1'

    _description = 'Report Customer Statement'

    def get_invoice_details(self, data, date_format):
        """Function call to get invoice."""
        partner_ids = self.env['res.partner'].browse(data['partner_ids'])
        partner_dict = {}
        start_date = data['start_date']
        end_date = data['end_date']
        # get all open invoice and credit not for opening balance.
        for partner in partner_ids:
            # Open Invoices
            open_invoices = self.env['account.invoice'].search([
                ('partner_id', '=', partner.id),
                ('type', '=', 'out_invoice'),
                ('state', '=', 'open'),
                ('date_invoice', '<', start_date),
            ])
            # Open Credit notes.
            open_credit_note = self.env['account.invoice'].search([
                ('partner_id', '=', partner.id),
                ('type', '=', 'out_refund'),
                ('state', '=', 'open'),
                ('date_invoice', '<', start_date),
            ])
            # Payment amount
            opening_balance = total_open_inv_amount = open_credit_amount = payment = 0.0
            # Get opening balance from journal(Miscellaneous Operations (USD))
            account_move = self.env['account.move'].search(
                [('journal_id', '=', 4), ('partner_id', '=', partner.id)])
            total_open_dr_amount = total_open_cr_amount = 0.0
            for move in account_move:
                total_open_dr_amount = sum(
                    [move_line.debit for move_line in move.line_ids.filtered(
                        lambda l: l.account_id.code == '1200') if move_line.debit != 0.0])
                total_open_cr_amount = sum(
                    [move_line.credit for move_line in move.line_ids.filtered(
                        lambda l: l.account_id.code == '1200') if move_line.credit != 0.0])
            total_open_move_amount = (
                total_open_dr_amount - total_open_cr_amount)
            if open_invoices:
                total_open_inv_amount = sum(
                    [inv.amount_total for inv in open_invoices])
            if open_credit_note:
                open_credit_amount = sum(
                    [inv.amount_total for inv in open_credit_note])
            for inv in open_invoices:
                for pay in inv.payment_ids.filtered(
                        lambda p: p.state == 'posted'):
                    payment += pay.amount or 0.0
            opening_balance = (
                total_open_inv_amount + total_open_move_amount - open_credit_amount - payment)
            # Get all invoices and credit notes between selected dates.
            for invoice in self.env['account.invoice'].search([
                    ('partner_id', '=', partner.id),
                    ('type', 'in', ['out_invoice', 'out_refund']),
                    ('state', 'not in', ['draft', 'cancel']),
                    ('date_invoice', '>=', start_date),
                    ('date_invoice', '<=', end_date)]):
                amount_total = 0.0
                if invoice.type == 'out_invoice':
                    amount_total = invoice.amount_total
                elif invoice.type == 'out_refund':
                    amount_total = -1 * invoice.amount_total
                vals_dict = {
                    'date_invoice': invoice.date_invoice.strftime(
                        date_format),
                    'name': invoice.number,
                    'amount_total': amount_total,
                    'residual': invoice.residual,
                    'partner_shipping_id': invoice.partner_shipping_id,
                    'payment': invoice.payment_ids,
                    'due_date': invoice.date_due,
                    'type': invoice.type
                }
                if partner not in partner_dict.keys():
                    partner_dict.update({
                        partner: {
                            'open_inv_amount': opening_balance,
                            'invoice_line': [vals_dict],
                        }
                    })
                else:
                    partner_dict[partner]['invoice_line'].append(vals_dict)
                    partner_dict[partner][
                        'open_inv_amount'] = opening_balance
                # partner_shipping_id = invoice.partner_shipping_id
            if partner not in partner_dict.keys():
                partner_dict.update({
                    partner: {'partner_shipping_id': partner}
                })
            if partner in partner_dict.keys() and not any(
                    [x for x in partner_dict[partner].get(
                        'invoice_line', []) if 'partner_shipping_id' in x.keys()]):
                partner_dict[partner].update({'partner_shipping_id': partner})
            # got periods date i.e 30,60,90 Days
            date_from = fields.Date.from_string(start_date)
            start = date_from
            stop_30days = stop_60days = stop_90days = ''
            for i in range(5)[::-1]:
                stop_30days = start - relativedelta(days=29)
                stop_60days = start - relativedelta(days=59)
                stop_90days = start - relativedelta(days=89)
            invoice_obj = self.env['account.invoice']
            # get 30days invoices
            domain_30days_invoice = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_invoice']),
                ('state', 'not in', ['draft', 'cancel']),
                ('date_invoice', '>=', stop_30days),
                ('date_invoice', '<=', start_date)])
            invoice_30days = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    domain_30days_invoice)])
            # get 30days Credit notes
            domain_30days_creditnote = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_refund']),
                ('state', 'not in', ['draft', 'cancel']),
                ('date_invoice', '>=', stop_30days),
                ('date_invoice', '<=', start_date)])
            creditnote_30days = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    domain_30days_creditnote)])
            # Get 60Dyas amount
            domain_60days_invoice = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_invoice']),
                ('state', 'not in', ['draft', 'cancel']),
                ('date_invoice', '<=', stop_30days),
                ('date_invoice', '>=', stop_60days)])
            invoice_60days = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    domain_60days_invoice)])
            # get 60Dyas Credit notes
            domain_60days_creditnote = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_refund']),
                ('state', 'not in', ['draft', 'cancel']),
                ('date_invoice', '<=', stop_30days),
                ('date_invoice', '>=', stop_60days)])
            creditnote_60days = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    domain_60days_creditnote)])
            # Get 90Dyas amount
            domain_90days_invoice = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_invoice']),
                ('state', 'not in', ['draft', 'cancel']),
                ('date_invoice', '<=', stop_60days),
                ('date_invoice', '>=', stop_90days)])
            invoice_90days = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    domain_90days_invoice)])
            # get 90Dyas Credit notes
            domain_90days_creditnote = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_refund']),
                ('state', 'not in', ['draft', 'cancel']),
                ('date_invoice', '<=', stop_60days),
                ('date_invoice', '>=', stop_90days)])
            creditnote_90days = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    domain_90days_creditnote)])
            # Get 90+Dyas amount
            domain_90plusdays_invoice = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_invoice']),
                ('state', 'not in', ['draft', 'cancel']),
                ('date_invoice', '<=', stop_90days)])
            invoice_90plusdays = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    domain_90plusdays_invoice)])
            # get 90+Dyas Credit notes
            domain_90plusdays_creditnote = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_refund']),
                ('state', 'not in', ['draft', 'cancel']),
                ('date_invoice', '<=', stop_90days)])
            creditnote_90plusdays = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    domain_90plusdays_creditnote)])
            on_account_cr_note = ([
                ('partner_id', '=', partner.id),
                ('type', 'in', ['out_refund']),
                ('state', 'in', ['open']),
                ('date_invoice', '<', start_date)])
            on_account = sum(
                [invoice.amount_total for invoice in invoice_obj.search(
                    on_account_cr_note)])
            # Sum of all 30,60,90 and 90+ invoices - credit notes
            between_30days = invoice_30days - creditnote_30days
            between_60days = invoice_60days - creditnote_60days
            between_90days = invoice_90days - creditnote_90days
            plus_90days = invoice_90plusdays - creditnote_90plusdays
            cust_dict = {
                'current_amount': 0.0,
                'between_30days': between_30days,
                'between_60days': between_60days,
                'between_90days': between_90days,
                'plus_90days': plus_90days,
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
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(partner_ids),
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
        }
