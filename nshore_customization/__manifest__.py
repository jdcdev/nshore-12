{
    'name': 'Nshore Customization',
    'version': '12.0.1.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'author': 'JDC system',
    'summary': 'Nshore Customization',
    'depends': ['sale', 'sale_management', 'account_reports', 'sale_margin', 'mail', 'contacts', 'web','stock', 'purchase', 'point_of_sale', 'account', 'web_digital_sign'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/nshore_customization_data.xml',
        'data/nshore_customization_product_qty.xml',
        'data/email_template_partner_statement.xml',
        'views/partner_view.xml',
        'views/template.xml',
        'views/inherited_sale_order.xml',
        'wizard/digital_signature_wizard.xml',
        'views/inherited_invoice_form.xml',
        'views/inherited_purchase_form.xml',
        'report/payment.xml',
        'views/inherited_product_product_view.xml',
        'views/inherited_product_template_view.xml',
        'views/inherited_stock_product_view.xml',
        'views/contact_views.xml',
        'views/report.xml',
        # 'views/res_users_view.xml',
        'wizard/account_report_customer_statement.xml',
        'wizard/daily_monthly_invoices_view.xml',
        'wizard/daily_monthly_payment_view.xml',
        'wizard/daily_monthly_returns_view.xml',
        'wizard/customer_purchases_views.xml',
        'wizard/update_invoice_line_views.xml',
        'wizard/wizard_inventory_adjustment_views.xml',
        'wizard/update_pricelist_item_view.xml',
        'wizard/open_po_report_wizard.xml',
        'report/report_registration.xml',
        'report/customer_statement_report.xml',
        'report/report_daily_monthly_invoices.xml',
        'report/report_daily_monthly_payment.xml',
        'report/report_daily_monthly_returns.xml',
        'report/report_sale_details.xml',
        'report/report_inventory_adjustment.xml',
        # 'report/report_open_purchase_order.xml',
        'report/report_inventory_valuation.xml',
        'report/customer_purchase_report_views.xml',
        'report/customer_purchase_report_detail_views.xml',
        'report/report_sale_order_view.xml',
        'report/report_invoice_extended.xml',
        'report/report_pricelist.xml',
        'report/customer_pricelist_reprot.xml',
        'report/report_open_po.xml',
        'views/customer_statement_unmail_views.xml',
        'views/menus.xml',
        'views/payment_terms.xml',
        'views/stock_move_line_view.xml',
        'views/stock_inventory_line_view.xml',
        'views/product_pricelist_view.xml',
        'views/res_company_view.xml',
        'views/account_portal_template_inherit.xml',
        'views/account_move_line_inherit_view.xml',
        'report/report_stock_level_forcast_list.xml',

    ],
    'qweb': [
        'static/src/xml/pos.xml',
        'static/src/xml/web_base.xml',
        'static/src/xml/base_import.xml'
    ],
    'installable': True,
    'auto_install': False,
}
