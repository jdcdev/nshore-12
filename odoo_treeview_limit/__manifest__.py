{
    'name': "Tree View Limit",

    'summary': 'Expand the limitations of default tree view',
    'description': """
    This module helps users to see all the records in the list view.
        """,

    'author': 'JDC Systems',
    'category': 'web',
    'version': '12.0.1.0.0',
    'license': "AGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'base'
    ],
    # always loaded
    'data': [
        'views/res_company_view.xml',
        'views/template.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
