from datetime import datetime, timedelta
from odoo import models, api


class CustomerPurchasesDetailReportView(models.AbstractModel):
    _name = 'report.nshore_customization.report_customer_purchase_detail'
    _description = 'Customer Purchases Detail Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        partner_contact_dict = {}
        partner_dict = {}
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        all_dates = docs.dates
        start_date = docs.start_date
        end_date = docs.end_date
        all_customer = docs.customer
        is_comparsion_reprot = docs.comparsion
        customer_id = docs.partner_id.id or None
        cust_phone = docs.pho_no or None
        area_code = docs.area_code or None
        all_products = docs.product
        product_id = docs.product_id.id or None
        product_category_id = docs.product_category_id.id or None
        vendor_id = docs.partner_vendor_id or None
        states = ('open', 'paid')
        invoice_types = 'out_invoice'
        sqlstr = """
            SELECT
                pc.id,
                pc.name AS category,
                pt.default_code AS default_code,
                pt.name AS description,
                MAX(i.date_invoice) AS last_purchased_date,
                SUM(l.quantity) AS quantity,
                SUM(l.price_subtotal) AS total_amount_purchased,
                SUM(l.price_unit) AS price,
                CAST(SUM(((pt.list_price - l.price_unit) / NULLIF(pt.list_price, 0)) * 100) As numeric(36,2)) AS total_discounts,
                SUM((l.price_unit - pt.net_cost) * l.quantity) AS total_gross_profit,
                CAST(SUM((((l.price_unit - pt.net_cost) * l.quantity) / NULLIF(l.price_unit, 0)) * 100) AS numeric(36,2)) as total_profit_margin,
                pt.list_price AS list_price,
                c.id,
                c.name,
                c.phone

            FROM account_invoice_line l
                LEFT JOIN account_invoice i ON (l.invoice_id = i.id)
                LEFT JOIN res_partner c ON (i.partner_id = c.id)
                LEFT JOIN product_product p ON (p.id=l.product_id)
                LEFT JOIN product_template pt ON (pt.id = p.product_tmpl_id)
                LEFT JOIN product_category pc ON (pt.categ_id = pc.id)
            """
        query_where = "where i.state in %s and i.type = %s"
        query_param = states, invoice_types
        if not all_dates:
            query_where += " AND (i.date_invoice IS NULL or (i.date_invoice>=%s and i.date_invoice<=%s))"
            query_param += start_date, end_date
        if not all_customer:
            if customer_id or area_code or cust_phone:
                query_where += " AND (i.partner_id = %s or c.zip = %s or c.phone = %s)"
                query_param += customer_id, area_code, cust_phone
        if not all_products:
            if product_id or product_category_id or vendor_id:
                query_where += ' AND (l.product_id = %s or pc.id = %s)'
                query_param += product_id, product_category_id
        groupby = "group by pc.id, pc.name,pt.default_code,pt.name,pt.list_price,c.id,c.name"
        final_sql_qry = sqlstr + ' ' + query_where + ' ' + groupby
        self.env.cr.execute(final_sql_qry, query_param)
        result = self.env.cr.fetchall()
        for res in result:
            vals_dict = {
                'default_code': res[2] or '',
                'description': res[3] or '',
                'last_purchased_date': res[4] or '',
                'qty': res[5] or 0.0,
                'total_amount_purchased': res[6] or 0.0,
                'price': res[7] or 0.0,
                'total_discounts': res[8] or 0.0,
                'total_gross_profit': res[9] or 0.0,
                'total_profit_margin': res[10] or 0.0,
                'list_price': res[11] or 0.0
            }
            if res[13] not in partner_dict.keys():
                partner_contact_dict.update({
                    res[13]:{'phone_no': res[14]}
                })
                partner_dict.update({
                    res[13]: {
                        res[1]: [vals_dict]
                    }
                })
            elif res[1] not in partner_dict[res[13]].keys():
                    partner_dict[res[13]].update({
                        res[1]: [vals_dict]
                    })
            else:
                partner_dict[res[13]][res[1]].append(vals_dict)
        data = {
            'doc_ids': self.ids,
            'doc_model': model,
            'partner_dict': partner_dict,
            'partner_contact_dict': partner_contact_dict,
            'start_date': docs.start_date,
            'end_date': docs.end_date,
            'currency_id': self.env.user.company_id.currency_id,
            'docs': docs,
        }
        return data
