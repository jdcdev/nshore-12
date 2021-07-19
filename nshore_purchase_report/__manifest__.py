{
    'name': 'Nshore Purchase Report',
    'version': '12.0.1.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'author': 'JDC Systems',
    'summary': 'In this module we have added customization in Delivery and Purchase Report.',
    'depends': [
        'nshore_customization'
    ],
    'data': [
        'report/purchase_order_template.xml',
        'report/purchase_quotation_template.xml',
        'report/picking_operations_template.xml',
        'report/delivery_slip_template.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
