#!/usr/bin/env python3
import xmlrpc.client

# Odoo connection details
url = 'http://localhost:8069'
db = 'vfs'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if uid:
    print(f"[OK] Authenticated as user ID: {uid}")
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # List of MuK modules in dependency order
    muk_modules = [
        'muk_web_group',
        'muk_web_chatter',
        'muk_web_dialog',
        'muk_web_appsbar',
        'muk_web_colors',
        'muk_web_refresh',
        'muk_web_theme',
    ]

    for module_name in muk_modules:
        # Find the module
        module_ids = models.execute_kw(db, uid, password,
            'ir.module.module', 'search',
            [[('name', '=', module_name)]])

        if module_ids:
            module_id = module_ids[0]

            # Get module state
            module_data = models.execute_kw(db, uid, password,
                'ir.module.module', 'read',
                [module_id], {'fields': ['name', 'state', 'installable']})

            state = module_data[0]['state']
            installable = module_data[0]['installable']

            print(f"\n{module_name}:")
            print(f"  State: {state}")
            print(f"  Installable: {installable}")

            # Force installable = True if false
            if not installable:
                print(f"  → Setting installable=True...")
                models.execute_kw(db, uid, password,
                    'ir.module.module', 'write',
                    [[module_id], {'installable': True}])

            # Install if not installed
            if state not in ['installed', 'to install', 'to upgrade']:
                print(f"  → Installing...")
                models.execute_kw(db, uid, password,
                    'ir.module.module', 'button_immediate_install',
                    [[module_id]])
                print(f"  [OK] Installed!")
            else:
                print(f"  [OK] Already {state}")
        else:
            print(f"\n[ERROR] {module_name}: NOT FOUND")

    print("\n" + "="*50)
    print("MuK Backend Theme installation completed!")
    print("Please refresh your browser to see the changes.")
else:
    print("[ERROR] Authentication failed!")
