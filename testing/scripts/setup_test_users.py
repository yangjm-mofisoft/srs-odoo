#!/usr/bin/env python3
"""
Setup Test Users for Asset Finance Module

Run this in Odoo shell:
docker-compose exec web python /odoo/odoo-bin shell -c /etc/odoo/odoo.conf -d odoo19

Then run:
exec(open('/mnt/extra-addons/../testing/scripts/setup_test_users_fixed.py').read())
"""

print("=" * 80)
print("SETTING UP TEST USERS FOR ASSET FINANCE MODULE")
print("=" * 80)

# Get company
company = env.company
print(f"\nUsing Company: {company.name} (ID: {company.id})")

# Define test users
test_users = [
    {
        'name': 'Test Finance Manager',
        'login': 'finance.manager',
        'password': 'test123',
        'email': 'finance.manager@test.com',
        'groups': ['asset_finance.group_finance_manager'],
    },
    {
        'name': 'Test Finance Officer',
        'login': 'finance.officer',
        'password': 'test123',
        'email': 'finance.officer@test.com',
        'groups': ['asset_finance.group_finance_officer'],
    },
    {
        'name': 'Test Collection Staff',
        'login': 'collection.staff',
        'password': 'test123',
        'email': 'collection.staff@test.com',
        'groups': ['asset_finance.group_collection_staff'],
    },
    {
        'name': 'Test All Roles',
        'login': 'finance.all',
        'password': 'test123',
        'email': 'finance.all@test.com',
        'groups': [
            'asset_finance.group_finance_manager',
            'asset_finance.group_finance_officer',
            'asset_finance.group_collection_staff',
        ],
    },
]

print("\n" + "=" * 80)
print("CREATING TEST USERS")
print("=" * 80)

for user_data in test_users:
    login = user_data['login']
    print(f"\n--- Processing: {login} ---")

    # Check if user already exists
    existing_user = env['res.users'].sudo().search([('login', '=', login)], limit=1)

    if existing_user:
        print(f"✓ User '{login}' already exists (ID: {existing_user.id})")
        user = existing_user
    else:
        # Create new user
        try:
            user = env['res.users'].sudo().create({
                'name': user_data['name'],
                'login': login,
                'password': user_data['password'],
                'email': user_data['email'],
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
            })
            print(f"✅ Created user: {user.name} (ID: {user.id})")
        except Exception as e:
            print(f"❌ Failed to create user '{login}': {e}")
            continue

    # Assign groups
    print(f"   Assigning groups to {login}...")
    for group_xmlid in user_data['groups']:
        try:
            group = env.ref(group_xmlid)
            # Check if group already assigned
            if group in user.group_ids:
                print(f"   ✓ Group '{group.name}' already assigned")
            else:
                user.sudo().write({'group_ids': [(4, group.id)]})
                print(f"   ✅ Assigned group: {group.name}")
        except Exception as e:
            print(f"   ❌ Failed to assign group '{group_xmlid}': {e}")

# Commit changes
try:
    env.cr.commit()
    print("\n" + "=" * 80)
    print("✅ ALL CHANGES COMMITTED TO DATABASE")
    print("=" * 80)
except Exception as e:
    print(f"\n❌ Failed to commit: {e}")
    env.cr.rollback()

# Verify users
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

for user_data in test_users:
    login = user_data['login']
    user = env['res.users'].sudo().search([('login', '=', login)], limit=1)

    if user:
        # Get Asset Finance groups
        af_groups = user.group_ids.filtered(
            lambda g: g.name in ['Finance Manager', 'Finance Officer', 'Collection Staff']
        )

        status = "✅" if af_groups else "⚠️"
        group_list = ", ".join(af_groups.mapped('name')) if af_groups else "NO GROUPS"

        print(f"{status} {login:20} → {group_list}")
    else:
        print(f"❌ {login:20} → NOT FOUND")

print("\n" + "=" * 80)
print("SETUP COMPLETE!")
print("=" * 80)
print("\nTest User Credentials:")
print("-" * 80)
for user_data in test_users:
    print(f"Login: {user_data['login']:20} Password: {user_data['password']}")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. Logout from Odoo")
print("2. Login as any test user (e.g., finance.manager / test123)")
print("3. You should see the 'Asset Finance' menu")
print("4. Click it to access the dashboard")
print("=" * 80)
