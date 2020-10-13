# -*- coding: utf-8 -*-

{
    'name': 'Update Account Invoice Taxes',
    'images': [],
    'summary': """Update existing invoices with taxes.""",
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': 'khyati/Atktiv',
    'website': 'http://www.onestein.eu',
    'license': 'AGPL-3',
    'depends': [
        'account', 'account_cancel'
    ],
    'data': [
        'wizard/res_partner_view.xml',
        'wizard/update_invoice_move_view.xml'
    ],
}
