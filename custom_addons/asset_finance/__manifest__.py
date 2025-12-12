{
    'name': 'Asset Financing Management',
    'version': '1.0.5',
    'category': 'Accounting/Leasing',
    'summary': 'Manage Asset Financing, HP, and Leasing Contracts',
    'author': 'Mofisoft PTE. LTD.',
    'depends': ['base', 'account', 'sale', 'purchase', 'fleet'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/test_users_data.xml',  # For testing user setup. Remove in production.
        'data/cron.xml',
        'data/finance_term_data.xml',
        'data/account_chart_data.xml',
        'data/account_config_data.xml',
        'data/mail_templates.xml',

        # --- 1. DEFINE ACTIONS FIRST ---
        'views/dashboard_views.xml',
        'views/asset_views.xml',
        'views/asset_sg_views.xml',
        # 'views/res_partner_contact_views.xml', # Security for new model
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/penalty_views.xml',
        'views/account_config_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/contract_views.xml',
        'wizard/settlement_views.xml',
        'wizard/disbursement_wizard_views.xml',
        'views/account_payment_views.xml',

        # --- 2. DEFINE MAIN MENU STRUCTURE ---
        'views/menu_views.xml',  # Creates 'menu_finance_config'

        # --- 3. ADD ITEMS TO THAT STRUCTURE ---
        'views/partner_menus.xml',
        'views/access_rights_views.xml',       # Adds 'Security' to 'menu_finance_config'
        'views/res_config_settings_views.xml', # Adds 'Settings' to 'menu_finance_config'
        'views/report_views.xml',
        
        'reports/finance_reports.xml',
        'reports/finance_contract_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'asset_finance/static/src/scss/dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}