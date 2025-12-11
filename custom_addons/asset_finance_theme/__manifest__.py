{
    'name': 'Asset Finance - Modern Bootstrap 5 Theme',
    'version': '1.0.0',
    'category': 'Theme/Backend',
    'summary': 'Modern Bootstrap 5 Admin Theme for Asset Finance Module',
    'description': """
        Modern Bootstrap 5 Theme for Asset Finance
        ===========================================

        This theme provides a complete UI transformation with:
        * Modern Bootstrap 5 styling
        * Responsive design
        * Beautiful color schemes
        * Enhanced dashboard
        * Smooth animations
        * Professional admin interface

        Compatible with Odoo 19 Asset Finance module.
    """,
    'author': 'Mofisoft PTE. LTD.',
    'depends': [
        'web',
        'asset_finance',
    ],
    'data': [
        'views/webclient_templates.xml',
        'views/assets.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # CSS Files (load in order)
            'asset_finance_theme/static/src/css/modern_theme.css',
            'asset_finance_theme/static/src/css/menu.css',
            'asset_finance_theme/static/src/css/forms.css',
            'asset_finance_theme/static/src/css/dashboard.css',
            'asset_finance_theme/static/src/css/components.css',
            # JavaScript
            'asset_finance_theme/static/src/js/theme.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
