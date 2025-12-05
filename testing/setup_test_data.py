# -------------------------------------------------------------------------
# UPDATED SCRIPT TO GENERATE TEST DATA FOR VEHICLE FINANCING (v5)
# Run this inside Odoo Shell
# -------------------------------------------------------------------------
import logging
from datetime import date

def run_setup(env):
    print("\n--- STARTING DATA SETUP (v5 - With Guarantors) ---")
    
    # 1. FORCE SUPERUSER & COMPANY CONTEXT
    user_id = env.ref('base.user_admin').id
    company = env['res.company'].search([], limit=1)
    if not company:
        company = env['res.company'].create({'name': 'My Company', 'currency_id': env.ref('base.USD').id})
    
    env = env(user=user_id, context={'allowed_company_ids': [company.id]})
    
    print(f"Using Company: {company.name} (ID: {company.id})")

    # 2. SETUP CHART OF ACCOUNTS
    def get_or_create_account(code, name, type_key):
        Account = env['account.account'].sudo()
        domain = [('code', '=', code)]
        if 'company_id' in Account._fields:
             domain.append(('company_id', '=', company.id))

        acc = Account.search(domain, limit=1)
        
        if not acc:
            print(f"Creating Account: {name} ({code})")
            vals = {
                'name': name,
                'code': code,
                'account_type': type_key,
                'reconcile': type_key in ['asset_receivable', 'liability_payable'],
            }
            if 'company_id' in Account._fields:
                vals['company_id'] = company.id
            acc = Account.create(vals)
        else:
            print(f"Found Account: {name} ({code})")
        return acc

    # Accounts
    asset_account = get_or_create_account('2002', 'HP Debtors (Principal)', 'asset_receivable')
    unearned_account = get_or_create_account('4002', 'Unearned Interest (Liability)', 'liability_current')
    income_account = get_or_create_account('5001', 'HP Interest Income', 'income')
    
    # Journal
    journal = env['account.journal'].sudo().search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
    if not journal:
        journal = env['account.journal'].sudo().create({
            'name': 'Customer Invoices', 'code': 'INV', 'type': 'sale', 'company_id': company.id
        })

    # 3. SETUP MASTER DATA
    Partner = env['res.partner'].sudo()
    
    # Dealer
    dealer_partner = Partner.search([('name', '=', 'Super Cars Dealership')], limit=1)
    if not dealer_partner:
        dealer_partner = Partner.create({'name': 'Super Cars Dealership', 'is_company': True})
    
    Dealer = env['leasing.dealer'].sudo()
    dealer = Dealer.search([('code', '=', 'D001')], limit=1)
    if not dealer:
        dealer = Dealer.create({'name': 'Super Cars', 'code': 'D001'})
    
    # Hirer
    hirer = Partner.search([('nric', '=', 'S1234567A')], limit=1)
    if not hirer:
        hirer = Partner.create({
            'name': 'John Doe (Test)',
            'email': 'john.doe@test.com',
            'nric': 'S1234567A',
            'street': '123 Orchard Road',
            'phone': '+65 9123 4567',
        })

    # --- NEW: GUARANTOR SETUP ---
    guarantor = Partner.search([('nric', '=', 'G9876543Z')], limit=1)
    if not guarantor:
        guarantor = Partner.create({
            'name': 'Gary Guarantor',
            'email': 'gary.g@test.com',
            'nric': 'G9876543Z',
            'street': '99 Guarantor Lane',
            'phone': '+65 8111 2222',
            'is_leasing_guarantor': True,  # Mark as guarantor
        })
    print(f"Guarantor: {guarantor.name}")

    # Vehicle
    Vehicle = env['leasing.vehicle'].sudo()
    vehicle = Vehicle.search([('reg_no', '=', 'SGA 8888 Z')], limit=1)
    if not vehicle:
        vehicle = Vehicle.create({
            'reg_no': 'SGA 8888 Z', 'make': 'Toyota', 'model': 'Camry', 'variant': '2.5 Hybrid',
            'year': 2024, 'fuel_type': 'hybrid', 'vehicle_type': 'passenger', 'status': 'available',
        })

    # 4. SETUP RULES & PRODUCT
    Penalty = env['leasing.penalty.rule'].sudo()
    penalty_rule = Penalty.search([('name', '=', 'Standard Late Interest 8%')], limit=1)
    if not penalty_rule:
        penalty_rule = Penalty.create({'name': 'Standard Late Interest 8%', 'method': 'daily_percent', 'rate': 8.0, 'grace_period_days': 3})

    Product = env['leasing.product'].sudo()
    product = Product.search([('name', '=', 'Standard HP 2025')], limit=1)
    if not product:
        product = Product.create({
            'name': 'Standard HP 2025', 'product_type': 'hp', 'default_int_rate': 5.0,
            'default_penalty_rule_id': penalty_rule.id, 'active': True
        })

    # 5. CREATE CONTRACT (With Guarantor)
    Contract = env['leasing.contract'].sudo()
    contract = Contract.search([('hirer_id', '=', hirer.id), ('vehicle_id', '=', vehicle.id)], limit=1)
    
    if not contract:
        # Using create([{}]) format for safety
        contract = Contract.create([{
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
            
            # --- ADDING GUARANTOR HERE ---
            'guarantor_ids': [(6, 0, [guarantor.id])]
        }])
        print(f"\nSUCCESS! Contract Created: {contract.agreement_no}")
    else:
        print(f"\nContract already exists: {contract.agreement_no}")
        # Update existing contract to include guarantor if missing
        if guarantor.id not in contract.guarantor_ids.ids:
            contract.write({'guarantor_ids': [(4, guarantor.id)]})
            print(f"Added Guarantor {guarantor.name} to existing contract.")

    print("------------------------------------------")
    env.cr.commit()

if __name__ == '__main__':
    run_setup(env)