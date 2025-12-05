# -------------------------------------------------------------------------
# UPDATED SCRIPT TO GENERATE TEST DATA FOR VEHICLE FINANCING (v3)
# Run this inside Odoo Shell
# -------------------------------------------------------------------------
import logging
from datetime import date

def run_setup(env):
    print("\n--- STARTING DATA SETUP (v3) ---")
    
    # 1. FORCE SUPERUSER & COMPANY CONTEXT
    # This prevents access right issues or missing company_id errors
    user_id = env.ref('base.user_admin').id
    company = env['res.company'].search([], limit=1)
    
    # Switch env to Admin + Correct Company
    env = env(user=user_id, context={'allowed_company_ids': [company.id]})
    
    print(f"Using Company: {company.name} (ID: {company.id})")

    # 2. SETUP CHART OF ACCOUNTS
    # ----------------------------------------
    def get_or_create_account(code, name, type_key):
        # Use sudo() to ensure we can read/write regardless of rules
        Account = env['account.account'].sudo()
        
        # Search for existing account
        # We search using integer ID for company to be safe
        domain = [('code', '=', code), ('company_id', '=', company.id)]
        acc = Account.search(domain, limit=1)
        
        if not acc:
            print(f"Creating Account: {name} ({code})")
            vals = {
                'name': name,
                'code': code,
                'account_type': type_key,
                'company_id': company.id,
                'reconcile': type_key in ['asset_receivable', 'liability_payable'],
            }
            acc = Account.create(vals)
        else:
            print(f"Found Account: {name} ({code})")
            
        return acc

    # Assets
    asset_account = get_or_create_account('2002', 'HP Debtors (Principal)', 'asset_receivable')
    
    # Liabilities
    unearned_account = get_or_create_account('4002', 'Unearned Interest (Liability)', 'liability_current')
    
    # Income
    income_account = get_or_create_account('5001', 'HP Interest Income', 'income')
    fee_account = get_or_create_account('5002', 'Processing Fee Income', 'income')
    settlement_income_account = get_or_create_account('5004', 'Early Settlement Income', 'income_other')

    # Get Sales Journal
    journal = env['account.journal'].sudo().search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
    if not journal:
        journal = env['account.journal'].sudo().create({
            'name': 'Customer Invoices',
            'code': 'INV',
            'type': 'sale',
            'company_id': company.id
        })
    print(f"Journal: {journal.name}")

    # 3. SETUP MASTER DATA
    # ----------------------------------------
    Partner = env['res.partner'].sudo()
    
    dealer_partner = Partner.search([('name', '=', 'Super Cars Dealership')], limit=1)
    if not dealer_partner:
        dealer_partner = Partner.create({'name': 'Super Cars Dealership', 'is_company': True})
    
    Dealer = env['leasing.dealer'].sudo()
    dealer = Dealer.search([('code', '=', 'D001')], limit=1)
    if not dealer:
        dealer = Dealer.create({'name': 'Super Cars', 'code': 'D001'})
    
    hirer = Partner.search([('nric', '=', 'S1234567A')], limit=1)
    if not hirer:
        hirer = Partner.create({
            'name': 'John Doe (Test)',
            'email': 'john.doe@test.com',
            'nric': 'S1234567A',
            'street': '123 Orchard Road',
            'phone': '+65 9123 4567',
        })

    Vehicle = env['leasing.vehicle'].sudo()
    vehicle = Vehicle.search([('reg_no', '=', 'SGA 8888 Z')], limit=1)
    if not vehicle:
        vehicle = Vehicle.create({
            'reg_no': 'SGA 8888 Z',
            'make': 'Toyota',
            'model': 'Camry',
            'variant': '2.5 Hybrid',
            'year': 2024,
            'fuel_type': 'hybrid',
            'vehicle_type': 'passenger',
            'color': 'Pearl White',
            'engine_no': 'ENG-TEST-001',
            'chassis_no': 'CHS-TEST-001',
            'status': 'available',
        })

    # 4. SETUP PENALTY RULE
    # ----------------------------------------
    Penalty = env['leasing.penalty.rule'].sudo()
    penalty_rule = Penalty.search([('name', '=', 'Standard Late Interest 8%')], limit=1)
    if not penalty_rule:
        penalty_rule = Penalty.create({
            'name': 'Standard Late Interest 8%',
            'method': 'daily_percent',
            'rate': 8.0,
            'grace_period_days': 3,
        })

    # 5. SETUP PRODUCT
    # ----------------------------------------
    Product = env['leasing.product'].sudo()
    product = Product.search([('name', '=', 'Standard HP 2025')], limit=1)
    if not product:
        product = Product.create({
            'name': 'Standard HP 2025',
            'product_type': 'hp',
            'default_int_rate': 5.0,
            'default_penalty_rule_id': penalty_rule.id,
            'active': True,
        })

    # 6. CREATE CONTRACT
    # ----------------------------------------
    Contract = env['leasing.contract'].sudo()
    contract = Contract.search([('hirer_id', '=', hirer.id), ('vehicle_id', '=', vehicle.id)], limit=1)
    if not contract:
        contract = Contract.create({
            'product_id': product.id,
            'hirer_id': hirer.id,
            'vehicle_id': vehicle.id,
            'agreement_date': date.today(),
            'finance_company_id': company.partner_id.id,
            
            'cash_price': 100000.0,
            'down_payment': 10000.0,
            'int_rate_pa': 5.0,
            'no_of_inst': 24, 
            'inst_day': 1,
            'interest_method': 'rule78',
            
            'dealer_id': dealer.id,
            'dealer_partner_id': dealer_partner.id,
            'admin_fee': 500.0,
            
            'journal_id': journal.id,
            'asset_account_id': asset_account.id,
            'income_account_id': income_account.id,
            'unearned_interest_account_id': unearned_account.id,
        })
        print(f"\nSUCCESS! Contract Created: {contract.agreement_no}")
    else:
        print(f"\nContract already exists: {contract.agreement_no}")

    print("------------------------------------------")
    env.cr.commit()

if __name__ == '__main__':
    run_setup(env)