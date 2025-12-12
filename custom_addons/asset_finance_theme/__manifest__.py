{
    'name': 'Asset Finance - Modern Theme',
    'version': '1.1.0',
    'category': 'Theme/Backend',
    'summary': 'Modern Bootstrap 5 Admin Theme for Asset Finance Module',
    'description': """
        Modern Bootstrap 5 Theme for Asset Finance
        ===========================================
        This theme provides a complete UI transformation with:
        * Full Bootstrap 5.3.2 integration
        * Modern responsive design
        * Beautiful color schemes
        * Enhanced dashboard components
        * Smooth animations and transitions
        * Professional admin interface
        * All Bootstrap 5 utilities and components available
        Compatible with Odoo 19 Asset Finance module.
    """,
    'author': 'Mofisoft PTE. LTD.',
    'depends': [
        'web',
        'asset_finance',
    ],
    'data': [
        'views/webclient_templates.xml',
    ],
    'assets': {
        # 1. Variables must be loaded first to override Odoo defaults
        'web._assets_primary_variables': [
            ('after', 'web/static/src/scss/primary_variables.scss', 'asset_finance_theme/static/src/scss/primary_variables.scss'),
        ],
        # 2. Backend Styles and Logic
        'web.assets_backend': [
            # Replaced the full bootstrap include with a targeted SCSS file
            'asset_finance_theme/static/src/scss/theme.scss', 
            'asset_finance_theme/static/src/js/theme.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}