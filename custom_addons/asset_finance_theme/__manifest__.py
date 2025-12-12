{
    'name': 'Asset Finance - Modern Theme',
    'version': '1.0.7',
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
        'views/assets.xml',
    ],
    'assets': {
        # Load primary variables FIRST - before Odoo's variables
        'web._assets_primary_variables': [
            ('after', 'web/static/src/scss/primary_variables.scss', 'asset_finance_theme/static/src/scss/primary_variables.scss'),
        ],
        # Load theme styles in BACKEND bundle (for main Odoo interface)
        'web.assets_backend': [
            # Bootstrap 5.3.2 - Pre-compiled CSS (Odoo 19 blocks SCSS @imports)
            'asset_finance_theme/static/src/bootstrap5.min.css',

            # Theme SCSS Files - Asset Finance custom styling
            'asset_finance_theme/static/src/webclient/**/*.scss',

            # JavaScript theme enhancements
            'asset_finance_theme/static/src/js/theme.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}