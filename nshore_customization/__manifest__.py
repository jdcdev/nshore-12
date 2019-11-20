
{
    'name': 'Nshore Customization',
    'version': '12.0.1.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'author': 'JDC system',
    'summary': 'Nshore Customization',
    'depends': [
        'sale_management', 'account_reports', 'sale_margin'
        , 'mail', 'contacts', 'web',
        'stock', 'purchase','point_of_sale', 'account'
    ],
    'data': [
        'data/nshore_customization_data.xml',
        'views/partner_view.xml',
        'security/security.xml',
        'views/template.xml',
        'views/inherited_sale_order.xml',
        'views/inherited_invoice_form.xml',
        'views/inherited_purchase_form.xml',
        'views/invoice_report.xml',
        'views/payment.xml',
        'views/inherited_product_product_view.xml',
        'views/inherited_product_template_view.xml',
        'views/report.xml',
        'wizard/account_report_customer_statement.xml',
        'wizard/daily_monthly_invoices_view.xml',
        'wizard/daily_monthly_payment_view.xml',
        'wizard/daily_monthly_returns_view.xml',
        'report/report_registration.xml',
        'report/customer_statement_report.xml',
        'report/report_daily_monthly_invoices.xml',
        'report/report_daily_monthly_payment.xml',
        'report/report_daily_monthly_returns.xml',
        'report/report_inventory_adjustment.xml',
        'report/report_open_purchase_order.xml',
        'report/report_inventory_listing.xml',
        'data/email_template_partner_statement.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
