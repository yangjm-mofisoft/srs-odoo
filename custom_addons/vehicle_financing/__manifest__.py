{
    'name': 'Vehicle Financing Management',
    'version': '1.0.0',
    'category': 'Accounting/Leasing',
    'summary': 'Manage Vehicle Assets, HP, and Leasing Contracts',
    'author': 'Mofisoft PTE. LTD.',
    'depends': ['base', 'account', 'sale', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}