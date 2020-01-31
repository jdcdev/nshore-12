from odoo import fields, models, api
from datetime import date


class CustomerPurchases(models.TransientModel):
    _name = 'customer.purchases'

    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Product')
    partner_vendor_id = fields.Many2one('res.partner', string='Vendor')
    product_category_id = fields.Many2one(
        'product.category', string='Product Category')
    start_date = fields.Date(string='Start Date', default=date.today())
    end_date = fields.Date(string='End Date', default=date.today())
    pho_no = fields.Char(string="Phone")
    area_code = fields.Char(string="Area Code")
    customer = fields.Boolean(string="All Customer")
    product = fields.Boolean(string="All Products", default=True)
    dates = fields.Boolean(string="All Dates")
    summary = fields.Boolean(string="Summary")
    comparsion = fields.Boolean(string="Comparsion")
    screen_view = fields.Boolean(string="Screen View")
    user_id = fields.Many2one("res.users", string="Salesperson")
    is_all_salesperson = fields.Boolean(string="All Salesperson")

    @api.onchange('area_code')
    def _onchange_area_code(self):
        if self.area_code:
            partners = self.env['res.partner'].search([('customer', '=', True)])
            partner_ids = []
            for partner in partners:
                if partner.zip and self.area_code in partner.zip:
                    partner_ids.append(partner.id)
            return {'domain': {'partner_id': [('id', 'in', partner_ids)]}}
        return {'domain': {'partner_id': [('is_company', '=', True), ('id', 'not in', [])]}}

    @api.onchange('pho_no')
    def _onchange_pho_no(self):
        if self.pho_no:
            partners = self.env['res.partner'].search([('customer', '=', True)])
            partner_ids = []
            for partner in partners:
                if partner.phone and self.pho_no in partner.phone:
                    partner_ids.append(partner.id)
            return {'domain': {'partner_id': [('id', 'in', partner_ids)]}}
        return {'domain': {'partner_id': [('is_company', '=', True), ('id', 'not in', [])]}}

    @api.multi
    def print_report(self):
        self.ensure_one()
        data = self.read([
            'partner_id',
            'product_id',
            'partner_vendor_id',
            'product_category_id',
            'start_date',
            'end_date',
            'pho_no',
            'area_code',
            'customer',
            'product',
            'dates',
            'summary',
            'comparsion',
            'screen_view',
            'user_id',
            'is_all_salesperson'
        ])[0]

        if self.product:
            self.partner_vendor_id = False
            self.product_id = False
            self.product_category_id = False

        if self.customer:
            self.partner_id = False
            self.pho_no = False
            self.area_code = False

        if not self.summary:
            self.comparsion = False

        if self.is_all_salesperson:
            self.user_id = False

        if self.summary:
            if self.screen_view:
                return self.env.ref(
                    'nshore_customization.action_customer_purchase_html'
                ).with_context(from_transient_model=True, html_report=True).report_action(
                    self, data=data)
            return self.env.ref(
                'nshore_customization.action_customer_purchase'
            ).with_context(from_transient_model=True).report_action(
                self, data=data)
        if not self.summary:
            if self.screen_view:
                return self.env.ref(
                    'nshore_customization.action_customer_purchase_detail_html'
                ).with_context(
                    from_transient_model=True, html_report=True).report_action(self, data=data)
            return self.env.ref(
                'nshore_customization.action_customer_purchase_detail'
            ).with_context(
                from_transient_model=True).report_action(self, data=data)

    @api.onchange('customer')
    def _onchange_customer(self):
        if self.customer:
            self.partner_id = False
            self.pho_no = False
            self.area_code = False
            self.user_id = False

    @api.onchange('is_all_salesperson')
    def _onchange_customer(self):
        if self.is_all_salesperson:
            self.user_id = False

    @api.onchange('product')
    def _onchange_product(self):
        if self.product:
            self.partner_vendor_id = False
            self.product_id = False
            self.product_category_id = False

    @api.onchange('dates')
    def _onchange_all_date(self):
        if self.dates:
            self.start_date = ''
            self.end_date = ''
            self.comparsion = False

    @api.onchange('summary')
    def _onchange_summary(self):
        if not self.summary:
            self.comparsion = False

    @api.onchange('comparsion')
    def _onchange_comparsion(self):
        if self.comparsion:
            self.dates = False
