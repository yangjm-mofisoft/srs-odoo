#!/usr/bin/env python3
"""
Script to assign Asset Finance groups to test users

Run this in Odoo shell:
docker-compose exec web python /odoo/odoo-bin shell -c /etc/odoo/odoo.conf -d odoo19

Then paste this entire file content or run:
exec(open('/mnt/extra-addons/asset_finance/scripts/assign_test_user_groups.py').read())
"""

print("=" * 80)
print("ASSIGNING ASSET FINANCE GROUPS TO TEST USERS")
print("=" * 80)

# Define user-group mappings
user_group_mapping = {
    'finance.manager': ['asset_finance.group_finance_manager'],
    'finance.officer': ['asset_finance.group_finance_officer'],
    'collection.staff': ['asset_finance.group_collection_staff'],
    'finance.all': [
        'asset_finance.group_finance_manager',
        'asset_finance.group_finance_officer',
        'asset_finance.group_collection_staff'
    ],
}

for login, group_xmlids in user_group_mapping.items():
    print(f"\n{'='*80}")
    print(f"Processing: {login}")
    print('='*80)

    # Find user
    user = env['res.users'].search([('login', '=', login)], limit=1)

    if not user:
        print(f"❌ User '{login}' not found. Skipping...")
        continue

    print(f"✅ Found user: {user.name} (ID: {user.id})")

    # Get groups to assign
    groups_to_assign = []
    for xmlid in group_xmlids:
        try:
            group = env.ref(xmlid)
            groups_to_assign.append(group)
            print(f"   📌 Will assign: {group.name}")
        except Exception as e:
            print(f"   ❌ Failed to find group {xmlid}: {e}")

    if not groups_to_assign:
        print(f"   ⚠️  No groups to assign!")
        continue

    # Assign groups
    try:
        for group in groups_to_assign:
            user.write({'group_ids': [(4, group.id)]})

        env.cr.commit()

        print(f"   ✅ Successfully assigned {len(groups_to_assign)} group(s)!")

        # Verify
        assigned_groups = user.group_ids.filtered(
            lambda g: g.name in ['Finance Manager', 'Finance Officer', 'Collection Staff']
        )
        print(f"   ✓ Verified groups:")
        for g in assigned_groups:
            print(f"      • {g.name}")

    except Exception as e:
        print(f"   ❌ Error assigning groups: {e}")
        env.cr.rollback()

print(f"\n{'='*80}")
print("ASSIGNMENT COMPLETE")
print('='*80)

# Final verification
print("\n📊 FINAL STATUS:")
for login in user_group_mapping.keys():
    user = env['res.users'].search([('login', '=', login)], limit=1)
    if user:
        af_groups = user.group_ids.filtered(
            lambda g: g.name in ['Finance Manager', 'Finance Officer', 'Collection Staff']
        )
        status = "✅" if af_groups else "❌"
        group_names = ", ".join(af_groups.mapped('name')) if af_groups else "NONE"
        print(f"{status} {login:20} → {group_names}")
    else:
        print(f"❌ {login:20} → USER NOT FOUND")

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("1. Logout from Odoo")
print("2. Login as: finance.manager / test123")
print("3. You should now see the 'Asset Finance' menu!")
print("="*80)
