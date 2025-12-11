# -------------------------------------------------------------------------
# UPDATED SCRIPT TO GENERATE TEST DATA FOR ASSET FINANCE (v7 - Strategy C)
# Run this inside Odoo Shell
# -------------------------------------------------------------------------
import logging
from datetime import date

def run_setup(env):
    print("\n--- STARTING DATA SETUP (v7 - With Guarantor/Joint Hirer Lines) ---")
    
    # 1. FORCE SUPERUSER & COMPANY CONTEXT
    user_id = env.ref('base.user_admin').id
    company = env['res.company'].search([], limit=1)
    if not company:
        company = env['res.company'].create({'name': 'My Company', 'currency_id': env.ref('base.USD').id})
    
    env = env(user=user_id, context={'allowed_company_ids': [company.id]})
    
    print(f"Using Company: {company.name} (ID: {company.id})")

    User = env['res.users'].sudo()

    # --- CREATE TEST USERS FOR GROUPS ---
    def create_test_user(name, login):
        user = User.search([('login', '=', login)], limit=1)
        if not user:
            user = User.create({
                'name': name,
                'login': login,
                'password': login, # Password same as login for testing
                'email': f"{login}@test.com",
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])]
            })
            print(f"Created User: {name} ({login})")
        return user

    create_test_user('Finance Manager', 'finance.manager')
    create_test_user('Finance Officer', 'finance.officer')
    create_test_user('Collection Staff', 'collection.staff')
    create_test_user('Super Finance User', 'finance.all')

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

    # 3. SETUP MASTER DATA (Partners & Asset)
    Partner = env['res.partner'].sudo()
    

    # Dealer
    dealer_partner = Partner.search([('name', '=', 'Super Cars Dealership')], limit=1)
    if not dealer_partner:
        dealer_partner = Partner.create({
            'name': 'Super Cars Dealership', 
            'is_company': True,
            'supplier_rank': 1
        })
    
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

    # Guarantor
    guarantor = Partner.search([('nric', '=', 'G9876543Z')], limit=1)
    if not guarantor:
        guarantor = Partner.create({
            'name': 'Gary Guarantor',
            'email': 'gary.g@test.com',
            'nric': 'G9876543Z',
            'street': '99 Guarantor Lane',
            'is_finance_guarantor': True,
        })
    print(f"Guarantor: {guarantor.name}")

    # Co-Borrower (Joint Hirer)
    co_borrower = Partner.search([('nric', '=', 'J7778889X')], limit=1)
    if not co_borrower:
        co_borrower = Partner.create({
            'name': 'Jane Joint-Hirer',
            'email': 'jane.j@test.com',
            'nric': 'J7778889X',
            'street': '123 Orchard Road', # Same as hirer
            'is_finance_joint_hirer': True,
        })
    print(f"Co-Borrower: {co_borrower.name}")

    # Asset
    Asset = env['finance.asset'].sudo()
    asset = Asset.search([('name', '=', 'Toyota Camry (SGA 8888 Z)')], limit=1)
    if not asset:
        asset = Asset.create({
            'name': 'Toyota Camry (SGA 8888 Z)',
            'asset_type': 'vehicle',
            'serial_no': 'CHASSIS-TEST-001',
            'status': 'available',
        })

    # 4. SETUP RULES, PRODUCT & TERM
    Penalty = env['finance.penalty.rule'].sudo()
    penalty_rule = Penalty.search([('name', '=', 'Standard Late Interest 8%')], limit=1)
    if not penalty_rule:
        penalty_rule = Penalty.create({'name': 'Standard Late Interest 8%', 'method': 'daily_percent', 'rate': 8.0, 'grace_period_days': 3})

    Product = env['finance.product'].sudo()
    product = Product.search([('name', '=', 'Standard HP 2025')], limit=1)
    if not product:
        product = Product.create({
            'name': 'Standard HP 2025', 'product_type': 'hp', 'default_int_rate': 5.0,
            'default_penalty_rule_id': penalty_rule.id, 'active': True
        })

    Term = env['finance.term'].sudo()
    term_24 = Term.search([('months', '=', 24)], limit=1)
    if not term_24:
        term_24 = Term.create({'months': 24})

    # 5. CREATE CONTRACT
    Contract = env['finance.contract'].sudo()
    contract = Contract.search([('hirer_id', '=', hirer.id), ('asset_id', '=', asset.id)], limit=1)
    
    if not contract:
        # Create dictionary for Guarantor Lines (One2many)
        guarantor_lines = [(0, 0, {
            'partner_id': guarantor.id,
            'relationship': 'business_partner',
            'income_verified': True,
            'remarks': 'Verified via Pay Slips'
        })]

        # Create dictionary for Co-Borrower Lines (One2many)
        joint_hirer_lines = [(0, 0, {
            'partner_id': co_borrower.id,
            'relationship': 'spouse',
            'share_percentage': 50.0
        })]

        contract = Contract.create([{
            'product_id': product.id,
            'hirer_id': hirer.id,
            'asset_id': asset.id,
            'agreement_date': date.today(),
            'finance_company_id': company.partner_id.id,
            
            'cash_price': 100000.0,
            'down_payment': 10000.0,
            'int_rate_pa': 5.0,
            'no_of_inst': term_24.id,
            'inst_day': 1,
            'interest_method': 'rule78',
            
            'supplier_id': dealer_partner.id,
            'admin_fee': 500.0,
            
            'journal_id': journal.id,
            'asset_account_id': asset_account.id,
            'income_account_id': income_account.id,
            'unearned_interest_account_id': unearned_account.id,
            
            # --- UPDATED: Using One2many Line format ---
            'guarantor_line_ids': guarantor_lines,
            'joint_hirer_line_ids': joint_hirer_lines
        }])
        print(f"\nSUCCESS! Contract Created: {contract.agreement_no}")
    else:
        print(f"\nContract already exists: {contract.agreement_no}")
        
        # Check if guarantor exists in lines, if not add them
        existing_guarantors = contract.guarantor_line_ids.mapped('partner_id')
        if guarantor not in existing_guarantors:
            contract.write({
                'guarantor_line_ids': [(0, 0, {
                    'partner_id': guarantor.id, 
                    'relationship': 'business_partner',
                    'income_verified': True
                })]
            })
            print(f"Added Guarantor {guarantor.name} to existing contract.")

    print("------------------------------------------")
    env.cr.commit()

if __name__ == '__main__':
    run_setup(env)