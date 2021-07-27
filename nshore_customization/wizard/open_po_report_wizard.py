# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class OpenPOReportWizard(models.TransientModel):
    """Class added to pass report details."""

    _name = 'open.po.report.wizard'
    _description = 'Open PO Report Wizard'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    partner_ids = fields.Many2many(
        'res.partner', string='Vendor', domain="[('is_company', '=', True)]")
    category_ids = fields.Many2many(
        'product.category', String="product Category")
    company_id = fields.Many2one(
        'res.company', String="Company",
        default=lambda self: self.env.user.company_id)
    all_vendor = fields.Boolean(string="All Vendor?", default=True)
    all_categ = fields.Boolean(string="All Category?", default=True)
    catgeory_partner = fields.Selection([
        ('partner', 'Partner'), ('category', 'Category')],
        string="Report for?", default='partner')

    def print_open_po_report(self):
        """It creates pdf reports for particular vendor."""
        data_dict = {}
        partner_list = []
        print(self.start_date, type(self.start_date))
        if self.start_date > self.end_date:
            raise UserError(
                _("Start date should not be greater than end date"))
        data = self.read([
            'start_date',
            'end_date',
            'all_vendor',
            'catgeory_partner',
            'all_categ'
        ])[0]
        start_date = data['start_date']
        end_date = data['end_date']
        all_vendor = data['all_vendor']
        catgeory_partner = data['catgeory_partner']
        partner_list = self.partner_ids.ids
        category_list = self.category_ids.ids
        all_categ = data['all_categ']
        data_dict.update({
            'partner_ids': list(set(partner_list)),
            'category_ids': list(set(category_list)),
            'start_date': start_date,
            'end_date': end_date,
            'all_vendor': all_vendor,
            'catgeory_partner': catgeory_partner,
            'all_categ': all_categ
        })
        return self.env.ref(
            'nshore_customization.action_report_open_po').report_action(
            self, data_dict)
