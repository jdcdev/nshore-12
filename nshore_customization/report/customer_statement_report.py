from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models


class payroll_advice_report(models.AbstractModel):
    _name = 'report.nshore_customization.report_customer_statement_1'

    _description = 'Report Customer Statement'

    def get_invoice_details(self, data, date_format):
        partner_ids = self.env['res.partner'].browse(data['partner_ids'])
        partner_dict = {}
        partner_shipping_id = False
        start_date = data['start_date']
        end_date = data['end_date']
        for partner in partner_ids:
            for invoice in self.env['account.invoice'].search([
                    ('partner_id', '=', partner.id),
                    ('state', '!=', 'draft'),
                    ('date_invoice', '>=', start_date),
                    ('date_invoice', '<=', end_date)]):
                vals_dict = {
                    'date_invoice': invoice.date_invoice.strftime(
                            date_format),
                    'name': invoice.name,
                    'amount_total': invoice.amount_total,
                    'residual': invoice.residual,
                    'partner_shipping_id': invoice.partner_shipping_id
                }
                if partner not in partner_dict.keys():
                    partner_dict.update({
                        partner: {
                            'invoice_line': [vals_dict]
                        }
                    })
                else:
                    partner_dict[partner]['invoice_line'].append(vals_dict)
                partner_shipping_id = invoice.partner_shipping_id
            if partner not in partner_dict.keys():
                partner_dict.update({
                    partner: {'partner_shipping_id': partner}
                })
            if partner in partner_dict.keys() and not any([x for x in partner_dict[partner].get('invoice_line', []) if 'partner_shipping_id' in x.keys()]):
                partner_dict[partner].update({'partner_shipping_id': partner})
            results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(include_nullified_amount=True)._get_partner_move_lines(['receivable'], start_date, 'posted', 30)
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
        partner_ids = data['partner_ids']
        lines_data = self.get_invoice_details(data, date_format)
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(partner_ids),
            'date': datetime.now().strftime(date_format),
            'lines_data': lines_data,
        }
