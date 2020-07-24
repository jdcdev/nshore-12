{
    'name': "Express Returns",

    'summary': 'Nshore Express return for delivery with credit note.',
    'description': """
    This module tracks product returns and also generate credit note..
        """,

    'author': 'JDC System',
    'category': 'sale',
    'version': '12.0.1.0.0',
    'license': "AGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'sale_management',
        'stock','purchase','nshore_customization'
    ],
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/return_sequence.xml',
        'views/return_order_view.xml',
        'views/return_reason_views.xml',
        'views/sale_order_view.xml',
	],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
