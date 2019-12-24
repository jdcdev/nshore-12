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
    product = fields.Boolean(string="All Products")
    dates = fields.Boolean(string="All Dates")
    summary = fields.Boolean(string="Summary")
    comparsion = fields.Boolean(string="Comparsion")
    screen_view = fields.Boolean(string="Screen View")

    @api.multi
    def print_report(self):
        self.ensure_one()
        data = {
            'model': self._name,
            'active_id': self.id
        }
        if self.summary:
            if self.screen_view:
                return self.env.ref('nshore_customization.action_customer_purchase_html').with_context(
                    from_transient_model=True).report_action(self, data=data)
            return self.env.ref('nshore_customization.action_customer_purchase').with_context(
                from_transient_model=True).report_action(self, data=data)
        if not self.summary:
            if self.screen_view:
                return self.env.ref('nshore_customization.action_customer_purchase_detail_html').with_context(
                    from_transient_model=True).report_action(self, data=data)
            return self.env.ref('nshore_customization.action_customer_purchase_detail').with_context(
                from_transient_model=True).report_action(self, data=data)

    @api.multi
    @api.onchange('customer')
    def _onchange_customer(self):
        if self.customer:
            self.partner_id = ''
            self.pho_no = ''
            self.area_code = ''

    @api.multi
    @api.onchange('product')
    def _onchange_product(self):
        if self.product:
            self.partner_vendor_id = ''
            self.product_id = ''
            self.product_category_id = ''

    @api.multi
    @api.onchange('dates')
    def _onchange_all_date(self):
        if self.dates:
            self.start_date = ''
            self.end_date = ''

    @api.multi
    @api.onchange('summary')
    def _onchange_summary(self):
        if not self.summary:
            self.comparsion = ''