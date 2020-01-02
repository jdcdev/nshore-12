from dateutil.relativedelta import relativedelta
from odoo import models, api
import datetime
from datetime import datetime


class CustomerPurchasesReportView(models.AbstractModel):
    _name = 'report.nshore_customization.report_customer_purchase'
    _description = 'Customer Purchases Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        vals = []
        model = self.env.context.get('active_model')
        docs = data
        grand_total_purchased_amount = 0.0
        grand_total_discounts = 0.0
        grand_total_gross_profit = 0.0
        grand_total_margin = 0.0
        grand_past_total_purchased_amount = 0.0
        grand_past_total_gross_profit = 0.0
        grand_past_total_margin = 0.0
        grand_total_changed_amount = 0.0
        grand_total_changed_per = 0.0
        all_dates = data['dates']
        start_date = datetime.strptime(data['start_date'], "%Y-%m-%d")
        end_date = datetime.strptime(data['end_date'], "%Y-%m-%d")
        all_customer = data['customer']
        customer_id = data['partner_id'][0] if data['partner_id'] else None
        cust_phone = data['pho_no'] or None
        area_code = data['area_code'] or None
        is_comparsion_reprot = data['comparsion']
        all_products = data['product']
        product_id = data['product_id'][0] if data['product_id'] else None
        product_category_id = data['product_category_id'][
            0] if data['product_category_id'] else None
        vendor_id = data['partner_vendor_id'][
            0] if data['partner_vendor_id'] else None
        states = ('open', 'paid')
        invoice_types = 'out_invoice'
        sqlstr = """
            select
                c.ref as cust_ref,
                c.name as customer_name,
                max(i.date_invoice) as last_purchased_date,
                sum(l.price_subtotal) as total_amount_purchased,
                sum(l.discount) as total_discounts,
                sum((l.price_unit - pt.net_cost) * l.quantity) as total_gross_profit,
                cast(sum((((l.price_unit - pt.net_cost) * l.quantity) / NULLIF(l.price_subtotal, 0)) * 100) as numeric(36,2)) as total_profit_margin,
                c.id as cust_id
            from account_invoice_line l
            left join account_invoice i on (l.invoice_id = i.id)
            left join res_partner c on (i.partner_id = c.id)
            left join product_product p on (p.id=l.product_id)
            left join product_template pt on (pt.id = p.product_tmpl_id)
            left join product_category categ on (categ.id = pt.categ_id)"""
        query_where = "where i.state in %s and i.type = %s"
        query_param = states, invoice_types
        if is_comparsion_reprot and start_date and end_date:
            past_year_start_date = start_date - relativedelta(years=1)
            past_year_end_date = end_date - relativedelta(years=1)
            past_query_where = query_where + \
                " AND (i.date_invoice IS NULL or (i.date_invoice>=%s and i.date_invoice<=%s))"
            past_query_param = states, invoice_types, past_year_start_date, past_year_end_date
        if not all_dates:
            query_where += " AND (i.date_invoice IS NULL or (i.date_invoice>=%s and i.date_invoice<=%s))"
            query_param += start_date, end_date
        if not all_customer:
            if customer_id or area_code or cust_phone:
                query_where += " AND (i.partner_id = %s or c.zip = %s or c.phone = %s)"
                query_param += customer_id, area_code, cust_phone
            if is_comparsion_reprot:
                past_query_where += " AND (i.partner_id = %s or c.zip = %s or c.phone = %s)"
                past_query_param += customer_id, area_code, cust_phone
        if not all_products:
            if product_id or product_category_id or vendor_id:
                query_where += ' AND (l.product_id = %s or categ.id = %s)'
                query_param += product_id, product_category_id
            if is_comparsion_reprot:
                past_query_where += ' AND (l.product_id = %s or categ.id = %s)'
                past_query_param += product_id, product_category_id
        query_groupby = "group by c.name, c.ref, c.id"
        final_sql_qry = sqlstr + ' ' + query_where + ' ' + query_groupby
        if is_comparsion_reprot:
            past_sql_qry = """
                with cuur_customer_purchase AS (
                    select
                        c.ref as cust_ref,
                        c.name as customer_name,
                        max(i.date_invoice) as last_purchased_date,
                        sum(l.price_subtotal) as total_amount_purchased,
                        sum(l.discount) as total_discounts,
                        sum((l.price_unit - pt.net_cost) * l.quantity) as total_gross_profit,
                        cast(sum((((l.price_unit - pt.net_cost) * l.quantity) / NULLIF(l.price_subtotal, 0)) * 100) as numeric(36,2)) as total_profit_margin,
                        c.id as cust_id
                        from account_invoice_line l
                        left join account_invoice i on (l.invoice_id = i.id)
                        left join res_partner c on (i.partner_id = c.id)
                        left join product_product p on (p.id=l.product_id)
                        left join product_template pt on (pt.id = p.product_tmpl_id)
                        left join product_category categ on (categ.id = pt.categ_id) """ + query_where + """ """ + query_groupby + """),
                past_customer_purchase AS (
                    select
                        c.ref as cust_ref,
                        c.name as customer_name,
                        max(i.date_invoice) as last_purchased_date,
                        sum(l.price_subtotal) as total_amount_purchased,
                        sum(l.discount) as total_discounts,
                        sum((l.price_unit - pt.net_cost) * l.quantity) as total_gross_profit,
                        cast(sum((((l.price_unit - pt.net_cost) * l.quantity) / NULLIF(l.price_subtotal, 0)) * 100) as numeric(36,2)) as total_profit_margin,
                        c.id as cust_id
                    from account_invoice_line l
                    left join account_invoice i on (l.invoice_id = i.id)
                    left join res_partner c on (i.partner_id = c.id)
                    left join product_product p on (p.id=l.product_id)
                    left join product_template pt on (pt.id = p.product_tmpl_id)
                    left join product_category categ on (categ.id = pt.categ_id)""" + past_query_where + """ """ + query_groupby + """)
                SELECT 
                cp.cust_ref AS cust_ref, 
                cp.customer_name AS customer_name, 
                cp.last_purchased_date AS last_purchased_date,
                cp.total_amount_purchased AS total_amount_purchased,
                cp.total_discounts AS total_discounts,
                cp.total_gross_profit AS total_gross_profit,
                cp.total_profit_margin AS total_profit_margin,
                pcp.total_amount_purchased AS past_total_amount_purchased,
                pcp.total_gross_profit AS past_total_gross_profit,
                pcp.total_profit_margin AS past_total_profit_margin
                from cuur_customer_purchase cp
                left join past_customer_purchase pcp on (pcp.cust_id = cp.cust_id)

                """
            past_query_param = query_param + past_query_param
            self.env.cr.execute(past_sql_qry, past_query_param)
            past_final_rec = self.env.cr.fetchall()
            for past_rec in past_final_rec:
                total_purchased_amount = past_rec[3] or 0.0
                past_total_purchased_amount = past_rec[7] or 0.0
                grand_total_purchased_amount += total_purchased_amount
                grand_total_discounts += past_rec[4] or 0.0
                grand_total_gross_profit += past_rec[5] or 0.0
                grand_total_margin += past_rec[6] or 0.0
                grand_past_total_purchased_amount += past_total_purchased_amount
                grand_past_total_gross_profit += past_rec[8] or 0.0
                grand_past_total_margin += past_rec[9] or 0.0
                total_changed_amount = total_purchased_amount - past_total_purchased_amount
                if past_total_purchased_amount > 0:
                    total_changed_per = round(
                        (total_changed_amount / past_total_purchased_amount) * 100, 2)
                vals.append({
                    'cust_ref': past_rec[0] or '',
                    'cust_name': past_rec[1] or '',
                    'purchased_date': past_rec[2] or '',
                    'total_purchased_amount': total_purchased_amount,
                    'total_discounts': past_rec[4] or 0.0,
                    'total_gross_profit': past_rec[5] or 0.0,
                    'total_margin': past_rec[6] or 0.0,
                    'past_total_purchased_amount': past_total_purchased_amount,
                    'past_total_gross_profit': past_rec[8] or 0.0,
                    'past_total_margin':  past_rec[9] or 0.0,
                    'total_changed_amount': total_changed_amount,
                    'total_changed_per': total_changed_per if grand_past_total_purchased_amount else 0.0
                })
            grand_total_changed_amount = grand_total_purchased_amount - \
                grand_past_total_purchased_amount
            if grand_past_total_purchased_amount > 0:
                grand_total_changed_per = round(
                    (grand_total_changed_amount / grand_past_total_purchased_amount) * 100, 2)
        if not is_comparsion_reprot:
            self.env.cr.execute(final_sql_qry, (query_param))
            result = self.env.cr.fetchall()
            for res in result:
                grand_total_purchased_amount += res[3] or 0.0
                grand_total_discounts += res[4] or 0.0
                grand_total_gross_profit += res[5] or 0.0
                grand_total_margin += res[6] or 0.0
                vals.append({
                    'cust_ref': res[0] or '',
                    'cust_name': res[1] or '',
                    'purchased_date': res[2] or '',
                    'total_purchased_amount': res[3] or 0.0,
                    'total_discounts': res[4] or 0.0,
                    'total_gross_profit': res[5] or 0.0,
                    'total_margin': res[6] or 0.0,
                    'past_total_purchased_amount': 0.0,
                    'past_total_gross_profit': 0.0,
                    'past_total_margin': 0.0,
                    'total_changed_amount': 0.0,
                    'total_changed_per': 0.0
                })
        data = {
            'doc_ids': self.ids,
            'doc_model': model,
            'purchase_rec': vals,
            'grand_total_purchased_amount': grand_total_purchased_amount,
            'grand_total_discounts': grand_total_discounts,
            'grand_total_gross_profit': grand_total_gross_profit,
            'grand_total_margin': grand_total_margin,
            'grand_past_total_purchased_amount': grand_past_total_purchased_amount,
            'grand_past_total_gross_profit': grand_past_total_gross_profit,
            'grand_past_total_margin': grand_past_total_margin,
            'grand_total_changed_amount': grand_total_changed_amount,
            'grand_total_changed_per': grand_total_changed_per,
            'start_date': start_date,
            'end_date': end_date,
            'currency_id': self.env.user.company_id.currency_id,
            'docs': docs,
        }
        return data
