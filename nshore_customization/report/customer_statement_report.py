from datetime import datetime

from odoo import api, models


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
        for partner in partner_ids:
            open_invoices = self.env['account.invoice'].search([
                ('partner_id', '=', partner.id),
                ('type', '=', 'out_invoice'),
                ('state', '=', 'open'),
                ('date_invoice', '<', start_date),
            ])
            total_open_inv_amount = 0.0
            if not open_invoices:
                account_move = self.env['account.move'].search(
                    [('journal_id', '=', 4), ('partner_id', '=', partner.id)])
                total_open_dr_amount = total_open_cr_amount = 0.0
                for move in account_move:
                    total_open_dr_amount = sum([move_line.debit for move_line in move.line_ids.filtered(lambda l: l.account_id.code == '1200') if move_line.debit != 0.0])
                    total_open_cr_amount = sum([move_line.credit for move_line in move.line_ids.filtered(lambda l: l.account_id.code == '1200') if move_line.credit != 0.0])
                total_open_inv_amount = total_open_dr_amount - total_open_cr_amount
            if open_invoices:
                total_open_inv_amount = sum(
                    [inv.amount_total for inv in open_invoices])
            for invoice in self.env['account.invoice'].search([
                    ('partner_id', '=', partner.id),
                    ('type', '=', 'out_invoice'),
                    ('state', '!=', 'draft'),
                    ('date_invoice', '>=', start_date),
                    ('date_invoice', '<=', end_date)]):
                vals_dict = {
                    'date_invoice': invoice.date_invoice.strftime(
                        date_format),
                    'name': invoice.number,
                    'state': invoice.state,
                    'amount_total': invoice.amount_total,
                    'residual': invoice.residual,
                    'partner_shipping_id': invoice.partner_shipping_id,
                    'payment': invoice.payment_ids
                }
                if partner not in partner_dict.keys():
                    partner_dict.update({
                        partner: {
                            'open_inv_amount': total_open_inv_amount,
                            'invoice_line': [vals_dict],
                        }
                    })
                else:
                    partner_dict[partner]['invoice_line'].append(vals_dict)
                    partner_dict[partner]['open_inv_amount'] = total_open_inv_amount
                # partner_shipping_id = invoice.partner_shipping_id
            if partner not in partner_dict.keys():
                partner_dict.update({
                    partner: {'partner_shipping_id': partner}
                })
            if partner in partner_dict.keys() and not any(
                    [x for x in partner_dict[partner].get(
                        'invoice_line', []) if 'partner_shipping_id' in x.keys()]):
                partner_dict[partner].update({'partner_shipping_id': partner})
            results, total, amls = self.env[
                'report.account.report_agedpartnerbalance'].with_context(
                include_nullified_amount=True)._get_partner_move_lines(
                ['receivable'], datetime.today(), 'posted', 30)
            for rec in results:
                if rec['partner_id'] == partner.id:
                    cust_dict = {
                        'current_amount': rec['direction'],
                        'between_30days': rec['4'],
                        'between_60days': rec['3'],
                        'between_90days': rec['2'],
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
