#!/usr/bin/env python3
"""Script to update Odoo module list and remove uninstalled modules"""

import odoo
from odoo.api import Environment
import sys

# Initialize Odoo
odoo.tools.config.parse_config(['-d', 'vfs', '-c', '/etc/odoo/odoo.conf'])

with odoo.api.Environment.manage():
    with odoo.registry('vfs').cursor() as cr:
        env = Environment(cr, odoo.SUPERUSER_ID, {})

        # Update module list - this will remove modules that no longer exist
        print("Updating module list...")
        env['ir.module.module'].update_list()

        # Find and remove any MuK modules that are still in the database
        muk_modules = env['ir.module.module'].search([
            ('name', 'ilike', 'muk_%')
        ])

        if muk_modules:
            print(f"Found {len(muk_modules)} MuK modules in database:")
            for module in muk_modules:
                print(f"  - {module.name} (state: {module.state})")

            # Remove them from database
            print("Removing MuK modules from database...")
            muk_modules.unlink()
        else:
            print("No MuK modules found in database.")

        cr.commit()
        print("✓ Module list updated successfully!")
