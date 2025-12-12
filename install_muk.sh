#!/bin/bash
# Install MuK Backend Theme modules

echo "Installing MuK Backend Theme..."

docker exec odoo-dev-web-1 python3 << 'PYTHON_SCRIPT'
import odoo
from odoo import api, SUPERUSER_ID

# Connect to database
registry = odoo.registry('vfs')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

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
        module = env['ir.module.module'].search([('name', '=', module_name)])

        if module:
            print(f"\n{module_name}:")
            print(f"  State: {module.state}")
            print(f"  Installable: {module.installable}")

            # Force installable = True
            if not module.installable:
                print(f"  -> Setting installable=True...")
                module.write({'installable': True})

            # Install if not installed
            if module.state not in ['installed', 'to install', 'to upgrade']:
                print(f"  -> Installing...")
                module.button_immediate_install()
                print(f"  [OK] Installed!")
            else:
                print(f"  [OK] Already {module.state}")
        else:
            print(f"\n[ERROR] {module_name}: NOT FOUND")

    cr.commit()
    print("\n" + "="*50)
    print("MuK Backend Theme installation completed!")
PYTHON_SCRIPT

echo ""
echo "Done! Please refresh your browser."
