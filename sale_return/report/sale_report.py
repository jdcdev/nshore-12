from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _name = "sale.return.report"
    _description = "Sales Return Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    return_name = fields.Char(string="Return Name")
    product_id = fields.Many2one("product.product",string="Product")
    sale_person = fields.Many2one("res.users", "Sale Person")
    date = fields.Date('Order Date', readonly=True)
    partner_id = fields.Many2one("res.partner", "Customer")
    reason_id = fields.Many2one("return.reason", "Reason Name")
    return_option = fields.Char(string="Return Option")
    total_amount = fields.Float(string="Amount", type="measure")
    order_id = fields.Many2one('sale.order', 'Order #', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'sale_return_report')
        self._cr.execute("""
            CREATE or replace VIEW sale_return_report AS(
                SELECT
                s.id as id,
                s.name as return_name,
                line.sale_order_id AS order_id,
                s.partner_id AS partner_id,
                s.date AS date,
                s.sale_person_id AS sale_person,
                s.reason_id AS reason_id ,
                line.return_option AS return_option,
                line.product_id as product_id,
                s.amount_total as total_amount
            FROM return_order as s
            LEFT JOIN return_order_line line on s.id=line.return_id
            GROUP BY order_id,s.id,line.return_option,line.product_id
            )""")
