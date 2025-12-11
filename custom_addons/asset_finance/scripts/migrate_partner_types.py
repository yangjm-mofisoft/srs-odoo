#!/usr/bin/env python3
"""
Migration Script: Convert Boolean Partner Flags to Single Selection Field

This script migrates data from the old boolean fields:
- is_finance_guarantor
- is_finance_broker
- is_finance_joint_hirer

To the new single selection field:
- finance_partner_type

Usage:
    docker-compose exec web odoo shell -d your_database_name

    Then in the Odoo shell:
    exec(open('/mnt/extra-addons/asset_finance/scripts/migrate_partner_types.py').read())
    migrate_partner_types(env)
"""

def migrate_partner_types(env):
    """
    Migrate partner type data from boolean fields to selection field.

    Final approach (4 business types only):
    - Brokers → 'broker'
    - Insurance companies → 'insurer' (manual)
    - Finance companies → 'finance_company' (manual)
    - Suppliers → 'supplier'
    - Customers/Guarantors/Co-Borrowers → NO TYPE (blank/False)

    Key principle: finance_partner_type is ONLY for specialized business entities.
    Partners WITHOUT a type can be customers/guarantors/co-borrowers (individual OR company).
    Use Odoo's 'Is a Company' checkbox to distinguish individuals from companies.

    Note: Same partner can be customer in one contract, guarantor in another, etc.
    """

    Partner = env['res.partner']
    Contract = env['finance.contract']

    print("\n" + "="*80)
    print("PARTNER TYPE MIGRATION - Simplified Approach")
    print("="*80 + "\n")

    total_migrated = 0

    # Step 1: Migrate brokers first (specific business role)
    print("✓ Step 1: Migrating Brokers...")
    if 'is_finance_broker' in Partner._fields:
        brokers = Partner.search([
            ('is_finance_broker', '=', True),
            ('finance_partner_type', '=', False)
        ])

        if brokers:
            print(f"  Setting {len(brokers)} partners as 'broker' (Sales Agent / Broker)")
            brokers.write({'finance_partner_type': 'broker'})
            total_migrated += len(brokers)

            # Show sample
            if len(brokers) <= 5:
                for p in brokers:
                    print(f"  - {p.name} (ID: {p.id})")
            else:
                for p in brokers[:3]:
                    print(f"  - {p.name} (ID: {p.id})")
                print(f"  ... and {len(brokers) - 3} more")
        else:
            print("  No brokers to migrate")

    print()

    # Step 2: Clear partner types for customers/guarantors/co-borrowers
    print("✓ Step 2: Clearing partner types for Customers/Guarantors/Co-Borrowers...")
    print("  Note: Customers, guarantors, and co-borrowers should have NO business type.")
    print("  Partners without a business type can act as customers/guarantors/co-borrowers (individuals OR companies).")

    # Get all partners from contracts (these are customers/guarantors/co-borrowers)
    hirers = Contract.search([]).mapped('hirer_id')
    guarantors = env['finance.contract.guarantor'].search([]).mapped('partner_id')
    co_borrowers = env['finance.contract.joint.hirer'].search([]).mapped('partner_id')

    all_customers = hirers | guarantors | co_borrowers

    # Also include partners with old boolean flags
    if 'is_finance_guarantor' in Partner._fields or 'is_finance_joint_hirer' in Partner._fields:
        flagged_partners = Partner.search([
            '|',
            ('is_finance_guarantor', '=', True),
            ('is_finance_joint_hirer', '=', True)
        ])
        all_customers |= flagged_partners

    # Filter to only those with a type that shouldn't have one
    # (exclude brokers, insurers, finance companies, suppliers)
    customers_with_wrong_type = all_customers.filtered(
        lambda p: p.finance_partner_type and p.finance_partner_type not in ['broker', 'insurer', 'finance_company', 'supplier']
    )

    if customers_with_wrong_type:
        print(f"  Clearing business type for {len(customers_with_wrong_type)} customer/guarantor/co-borrower partners")
        customers_with_wrong_type.write({'finance_partner_type': False})
        total_migrated += len(customers_with_wrong_type)

        # Show sample
        if len(customers_with_wrong_type) <= 5:
            for p in customers_with_wrong_type:
                print(f"  - {p.name} (ID: {p.id})")
        else:
            for p in customers_with_wrong_type[:3]:
                print(f"  - {p.name} (ID: {p.id})")
            print(f"  ... and {len(customers_with_wrong_type) - 3} more")
    else:
        print("  All customer/guarantor/co-borrower partners already have correct type (blank)")

    print()

    # Step 3: Set suppliers based on supplier_rank
    print("✓ Identifying suppliers from supplier_rank...")
    suppliers = Partner.search([
        ('supplier_rank', '>', 0),
        ('finance_partner_type', '=', False)
    ])

    if suppliers:
        print(f"  Setting {len(suppliers)} partners as 'supplier' (Supplier / Dealer)")
        suppliers.write({'finance_partner_type': 'supplier'})
        total_migrated += len(suppliers)

        # Show sample
        if len(suppliers) <= 5:
            for p in suppliers:
                print(f"  - {p.name} (ID: {p.id})")
        else:
            for p in suppliers[:3]:
                print(f"  - {p.name} (ID: {p.id})")
            print(f"  ... and {len(suppliers) - 3} more")
    else:
        print("  No suppliers to migrate")

    print()

    # Step 4: Commit the changes
    env.cr.commit()

    # Step 5: Summary statistics
    print("="*80)
    print("MIGRATION SUMMARY")
    print("="*80)
    print(f"Total partners migrated: {total_migrated}\n")

    # Count by type
    print("Partner Type Distribution:")
    print("  (No Business Type) - Customers/Guarantors/Co-Borrowers:")
    no_type_count = Partner.search_count([('finance_partner_type', '=', False)])
    print(f"    {no_type_count:5} partners without business type (can be hirers/guarantors/co-borrowers)")
    print()

    for type_value, type_label in [
        ('broker', 'Sales Agent / Broker'),
        ('insurer', 'Insurance Company'),
        ('finance_company', 'Finance Company'),
        ('supplier', 'Supplier / Dealer'),
    ]:
        count = Partner.search_count([('finance_partner_type', '=', type_value)])
        if count > 0:
            print(f"  {type_label:40} {count:5} partners")

    # Show note about no-type partners
    if no_type_count > 0:
        print(f"\n  Note: {no_type_count} partners with NO business type can act as:")
        print(f"        - Customers (Hirers) - both individuals and companies")
        print(f"        - Guarantors - both individuals and companies")
        print(f"        - Co-Borrowers - both individuals and companies")
        print(f"        The same partner can have different roles in different contracts.")
        print(f"        Use Odoo's 'Is a Company' checkbox to distinguish individuals from companies.")

    print("\n" + "="*80)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")

    print("Next steps:")
    print("1. Review the migrated data in Odoo UI")
    print("2. Manually classify any unmigrated partners if needed")
    print("3. After verification, you can remove the deprecated boolean fields from res_partner.py")
    print("4. Upgrade the module to apply all changes\n")


def rollback_migration(env):
    """
    ROLLBACK: Convert finance_partner_type back to boolean fields (for testing)

    WARNING: This will OVERWRITE the boolean fields with data from finance_partner_type.
    Only use this for testing or if you need to rollback the migration.
    """

    Partner = env['res.partner']

    print("\n" + "="*80)
    print("ROLLBACK MIGRATION - Starting...")
    print("="*80 + "\n")

    # Clear all boolean fields first
    print("Clearing old boolean fields...")
    all_partners = Partner.search([])
    all_partners.write({
        'is_finance_guarantor': False,
        'is_finance_broker': False,
        'is_finance_joint_hirer': False,
    })

    # Map back from selection to booleans
    mappings = [
        ('guarantor', 'is_finance_guarantor'),
        ('broker', 'is_finance_broker'),
        ('co_borrower', 'is_finance_joint_hirer'),
    ]

    for type_value, boolean_field in mappings:
        partners = Partner.search([('finance_partner_type', '=', type_value)])
        if partners:
            print(f"Setting {boolean_field} = True for {len(partners)} partners")
            partners.write({boolean_field: True})

    env.cr.commit()
    print("\n✅ Rollback completed\n")


# For easy testing
if __name__ == '__main__':
    print("This script should be run from within Odoo shell")
    print("\nUsage:")
    print("  docker-compose exec web odoo shell -d your_database_name")
    print("  exec(open('/mnt/extra-addons/asset_finance/scripts/migrate_partner_types.py').read())")
    print("  migrate_partner_types(env)")
