import random
from datetime import date, timedelta

# 1. Setup Environment References
Account = env['account.account']
Journal = env['account.journal']
Partner = env['res.partner']
Product = env['finance.product']
Asset = env['finance.asset']
Contract = env['finance.contract']
Term = env['finance.term']

# --- HELPER: Find required accounts/journals (Adjust codes/names as per your COA) ---
company = env.company
journal = Journal.search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
if not journal:
    raise Exception("No Sales Journal found! Please create one first.")

# Try to find standard accounts, fallback to creating simple ones if needed
def get_or_create_account(code, name, type_code):
    acc = Account.search([('code', '=', code), ('company_id', '=', company.id)], limit=1)
    if not acc:
        # Fallback search by type if specific code not found
        acc = Account.search([('account_type', '=', type_code), ('company_id', '=', company.id)], limit=1)
    return acc

asset_account = get_or_create_account('101200', 'Hire Purchase Debtors', 'asset_receivable')
income_account = get_or_create_account('400000', 'Interest Income', 'income')
unearned_account = get_or_create_account('201000', 'Unearned Interest', 'liability_current')

if not (asset_account and income_account and unearned_account):
    raise Exception("Missing required accounts (Asset/Income/Liability). Please ensure Chart of Accounts is installed.")

# --- 1. CREATE FINANCIAL PRODUCT ---
# Logic: Min Downpayment 30% = Max Finance 70%
#        Max Downpayment 90% = Min Finance 10%
hp_product = Product.create({
    'name': 'Standard Hire Purchase',
    'product_type': 'hp',
    'active': True,
    'default_int_rate': 2.5,
    'max_finance_percent': 70.0, # Corresponds to Min Downpayment 30%
    'min_finance_percent': 10.0, # Corresponds to Max Downpayment 90%
    'min_months': 12,
    'max_months': 60,
})
print(f"Created Product: {hp_product.name}")

# --- 2. CREATE CUSTOMERS (10 Total: 7 Indiv, 3 Company) ---
customers = []

# 7 Individuals
indiv_names = ['John Doe', 'Alice Smith', 'Bob Johnson', 'Charlie Brown', 'Diana Prince', 'Evan Wright', 'Fiona Green']
for name in indiv_names:
    p = Partner.create({
        'name': name,
        'is_company': False,
        'email': f"{name.replace(' ', '.').lower()}@example.com",
        'phone': '91234567',
        'street': '123 Orchard Road',
        'city': 'Singapore',
        'finance_partner_type': False # Regular customer
    })
    customers.append(p)

# 3 Companies
comp_names = ['Acme Logistics Pte Ltd', 'Beta Trading LLP', 'Gamma Construction Ltd']
for name in comp_names:
    p = Partner.create({
        'name': name,
        'is_company': True,
        'email': 'contact@company.com',
        'phone': '61234567',
        'street': '88 Shenton Way',
        'city': 'Singapore',
        'finance_partner_type': False # Regular customer
    })
    customers.append(p)

print(f"Created {len(customers)} Customers")

# --- 3. CREATE ASSETS (5 Vehicles) ---
# We create them directly as finance.asset to avoid Fleet dependency complexity, 
# but we fill in the smart fields manually.
vehicles_data = [
    ('Toyota Camry', 'SGA1234A', 'Toyota', 'Camry', 100000),
    ('Honda Civic', 'SGB5678B', 'Honda', 'Civic', 90000),
    ('Nissan NV200', 'SGC9012C', 'Nissan', 'NV200', 60000),
    ('Mercedes C180', 'SGD3456D', 'Mercedes', 'C180', 180000),
    ('BMW 320i', 'SGE7890E', 'BMW', '320i', 200000),
]

assets = []
for name, reg, make, model, price in vehicles_data:
    a = Asset.create({
        'name': name,
        'asset_type': 'vehicle',
        'status': 'available',
        'registration_no': reg,
        'make': make,
        'model': model,
        'chassis_no': f"CHS-{reg}",
        'engine_no': f"ENG-{reg}",
        'vehicle_condition': 'new',
    })
    assets.append(a)

print(f"Created {len(assets)} Assets")

# --- 4. PREPARE CONTRACT DATA ---
# Ensure a term exists (e.g., 24 Months)
term_24 = Term.search([('months', '=', 24)], limit=1)
if not term_24:
    term_24 = Term.create({'name': '24 Months', 'months': 24})

# --- CONTRACT 1: Individual + 2 Guarantors ---
# Product: HP Act (Usually < $55k loan) or Standard. 
# Asset: Honda Civic ($90k)
# Downpayment: 30% ($27k) -> Loan $63k
c1 = Contract.create({
    'company_id': company.id,
    'application_type': 'hp',
    'product_id': hp_product.id,
    'asset_id': assets[1].id, # Honda Civic
    'hirer_id': customers[0].id, # John Doe
    'agreement_date': date.today(),
    'first_due_date': date.today() + timedelta(days=30),
    
    # Financials
    'cash_price': 90000,
    'down_payment': 27000, # 30%
    'int_rate_pa': 2.5,
    'no_of_inst': term_24.id,
    'interest_method': 'rule78',
    'payment_scheme': 'arrears',
    
    # Accounts
    'journal_id': journal.id,
    'asset_account_id': asset_account.id,
    'income_account_id': income_account.id,
    'unearned_interest_account_id': unearned_account.id,
    
    # Guarantors
    'guarantor_line_ids': [
        (0, 0, {'partner_id': customers[1].id, 'relationship': 'spouse'}), # Alice
        (0, 0, {'partner_id': customers[2].id, 'relationship': 'sibling'}), # Bob
    ]
})
print(f"Created Contract 1: {c1.agreement_no} (Indiv + 2 Guarantors)")

# --- CONTRACT 2: Company Customer ---
# Asset: Nissan NV200 ($60k)
# Downpayment: 40% ($24k) -> Loan $36k
c2 = Contract.create({
    'company_id': company.id,
    'application_type': 'hp',
    'product_id': hp_product.id,
    'asset_id': assets[2].id, # Nissan
    'hirer_id': customers[7].id, # Acme Logistics (Index 7 is the first company)
    'agreement_date': date.today(),
    'first_due_date': date.today() + timedelta(days=30),
    
    # Financials
    'cash_price': 60000,
    'down_payment': 24000, # 40%
    'int_rate_pa': 2.5,
    'no_of_inst': term_24.id,
    'interest_method': 'flat',
    'payment_scheme': 'arrears',
    
    # Accounts
    'journal_id': journal.id,
    'asset_account_id': asset_account.id,
    'income_account_id': income_account.id,
    'unearned_interest_account_id': unearned_account.id,
})
print(f"Created Contract 2: {c2.agreement_no} (Company Customer)")

# Calculate financials for both contracts
c1._compute_financials()
c1._compute_installment_amounts()
c2._compute_financials()
c2._compute_installment_amounts()

# Generate Schedules
c1.action_generate_schedule()
c2.action_generate_schedule()

env.cr.commit()
print("Commit successful. Test data generated.")