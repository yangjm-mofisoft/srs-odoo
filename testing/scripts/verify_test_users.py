#!/usr/bin/env python3
"""
Verification script for test users

Run this in Odoo shell to verify test users were created correctly:
docker-compose exec web python /odoo/odoo-bin shell -c /etc/odoo/odoo.conf -d odoo19

Then in the shell:
exec(open('/mnt/extra-addons/asset_finance/scripts/verify_test_users.py').read())
"""

print("=" * 80)
print("VERIFYING TEST USERS FOR ASSET FINANCE MODULE")
print("=" * 80)

# Get the test users
test_user_logins = ['finance.manager', 'finance.officer', 'collection.staff', 'finance.all']

for login in test_user_logins:
    print(f"\n{'='*80}")
    print(f"USER: {login}")
    print('='*80)

    user = env['res.users'].search([('login', '=', login)], limit=1)

    if not user:
        print(f"❌ User '{login}' NOT FOUND!")
        continue

    print(f"✅ User found: {user.name} (ID: {user.id})")
    print(f"   Email: {user.email}")
    print(f"   Active: {user.active}")

    # Get all groups
    print(f"\n📋 GROUPS ({len(user.group_ids)} total):")

    # Get Asset Finance groups specifically
    asset_finance_groups = user.group_ids.filtered(
        lambda g: g.name in ['Finance Manager', 'Finance Officer', 'Collection Staff']
    )

    if asset_finance_groups:
        print(f"\n   ✅ ASSET FINANCE GROUPS:")
        for group in asset_finance_groups:
            privilege = group.privilege_id.name if group.privilege_id else 'No Privilege'
            print(f"      • {group.name} (Privilege: {privilege})")
    else:
        print(f"\n   ❌ NO ASSET FINANCE GROUPS ASSIGNED!")

    # Check implied groups
    print(f"\n   📌 Other Key Groups:")
    key_groups = [
        'Accounting / Manager',
        'Accounting / Billing',
        'User types / Internal User',
    ]

    for key_group_name in key_groups:
        has_group = any(key_group_name in g.full_name for g in user.group_ids)
        status = "✅" if has_group else "❌"
        print(f"      {status} {key_group_name}")

print(f"\n{'='*80}")
print("VERIFICATION COMPLETE")
print('='*80)

# Summary
print("\n📊 SUMMARY:")
for login in test_user_logins:
    user = env['res.users'].search([('login', '=', login)], limit=1)
    if user:
        af_groups = user.group_ids.filtered(
            lambda g: g.name in ['Finance Manager', 'Finance Officer', 'Collection Staff']
        )
        status = "✅" if af_groups else "❌"
        group_names = ", ".join(af_groups.mapped('name')) if af_groups else "None"
        print(f"{status} {login:20} → {group_names}")
    else:
        print(f"❌ {login:20} → NOT FOUND")

print("\n" + "="*80)
print("To fix missing groups, run:")
print("="*80)
print("""
# For finance.manager:
user = env['res.users'].search([('login', '=', 'finance.manager')])
user.write({'group_ids': [(4, env.ref('asset_finance.group_finance_manager').id)]})
env.cr.commit()

# For finance.officer:
user = env['res.users'].search([('login', '=', 'finance.officer')])
user.write({'group_ids': [(4, env.ref('asset_finance.group_finance_officer').id)]})
env.cr.commit()

# For collection.staff:
user = env['res.users'].search([('login', '=', 'collection.staff')])
user.write({'group_ids': [(4, env.ref('asset_finance.group_collection_staff').id)]})
env.cr.commit()
""")
