
{
    'name': 'Nshore Website',
    'version': '12.0.1.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'author': 'JDC Systems',
    'summary': 'Nshore Website',
    'depends': [
        'website', 'website_crm'
    ],
    'data': [
        'data/nshore_website_data.xml',
        'views/template.xml',
        'views/home.xml',
        'views/about_us.xml',
        'views/website_crm_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
}
