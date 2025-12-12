#!/usr/bin/env python3
import xmlrpc.client

# Odoo connection details
url = 'http://localhost:8069'
db = 'odoo_db'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if uid:
    print(f"Authenticated as user ID: {uid}")

    # Connect to object endpoint
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Find the asset_finance_theme module
    module_ids = models.execute_kw(db, uid, password,
        'ir.module.module', 'search',
        [[('name', '=', 'asset_finance_theme')]])

    if module_ids:
        print(f"Found module ID: {module_ids[0]}")

        # Upgrade the module
        models.execute_kw(db, uid, password,
            'ir.module.module', 'button_immediate_upgrade',
            [module_ids])

        print("Module upgraded successfully!")
    else:
        print("Module not found!")
else:
    print("Authentication failed!")
