# Running Test Data Script on Ubuntu Server

## Issue Fixed

The original script failed with error:
```
ValueError: Invalid field account.account.company_id in condition ('company_id', '=', 1)
```

**Root Cause:** The `account.account` model in some Odoo configurations doesn't have a `company_id` field, or it's not searchable in the same way.

**Fix Applied:** Updated the `get_or_create_account()` function to search without company filters, making it compatible with all Chart of Accounts configurations.

---

## How to Run on Ubuntu Server

### Option 1: Using the Shell Script (Recommended)

```bash
cd ~/srs-odoo
sudo sh run_test_data.sh
```

Or specify a different database:
```bash
sudo sh run_test_data.sh my_database_name
```

### Option 2: Manual Execution

```bash
cd ~/srs-odoo

# Copy script to mounted directory
cp testing/scripts/setup_test_data_02_enhanced.py custom_addons/

# Run in Odoo shell
docker-compose exec -T web ./odoo-bin shell \
  -c /etc/odoo/odoo.conf \
  -d vfs \
  --db_host=db \
  --no-http < custom_addons/setup_test_data_02_enhanced.py

# Clean up
rm custom_addons/setup_test_data_02_enhanced.py
```

### Option 3: Interactive Shell (For Debugging)

```bash
cd ~/srs-odoo

# Enter Odoo shell
docker-compose exec web ./odoo-bin shell -c /etc/odoo/odoo.conf -d vfs --db_host=db

# You'll get a Python prompt (>>>)
# Copy and paste the script contents, or:
exec(open('/mnt/extra-addons/setup_test_data_02_enhanced.py').read())
```

---

## What Changed in the Fix

### Before (Caused Error):
```python
def get_or_create_account(code, name, type_code):
    acc = Account.search([('code', '=', code), ('company_id', '=', company.id)], limit=1)
    if not acc:
        acc = Account.search([('account_type', '=', type_code), ('company_id', '=', company.id)], limit=1)
    return acc
```

### After (Fixed):
```python
def get_or_create_account(code, name, type_code):
    try:
        acc = Account.search([('code', '=', code)], limit=1)
        if not acc:
            acc = Account.search([('account_type', '=', type_code)], limit=1)
    except:
        acc = Account.search([('account_type', '=', type_code)], limit=1)
    return acc
```

**Key Changes:**
- Removed `company_id` filter from account searches
- Added try-except for robustness
- Searches by code first, then by account type

Similarly for journal searches:
```python
try:
    sales_journal = Journal.search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
    bank_journal = Journal.search([('type', '=', 'bank'), ('company_id', '=', company.id)], limit=1)
except:
    sales_journal = Journal.search([('type', '=', 'sale')], limit=1)
    bank_journal = Journal.search([('type', '=', 'bank')], limit=1)
```

---

## Prerequisites (Same as Before)

1. **Docker containers running:**
   ```bash
   docker-compose ps
   # Should show web and db containers as "Up"
   ```

2. **Database exists:** `vfs` database should be created

3. **Asset Finance module installed:**
   - Log into Odoo
   - Go to Apps
   - Search for "Asset Financing Management"
   - Click Install

4. **Chart of Accounts installed:**
   - Go to Accounting > Configuration > Chart of Accounts
   - If empty, install a chart (Settings > Accounting > Fiscal Localization)

5. **Journals exist:**
   - Accounting > Configuration > Journals
   - Need at least one "Sales" and one "Bank" journal

---

## Expected Output

```
==================================================
Running Enhanced Test Data Setup Script
Database: vfs
==================================================
2025-12-12 10:46:01,656 222 INFO ? odoo: Odoo version 19.1a1
2025-12-12 10:46:01,656 222 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
...
2025-12-12 10:46:03,249 222 INFO vfs odoo.registry: Registry loaded in 1.006s

=== Asset Finance Test Data Setup (Enhanced) ===

1. Creating Financial Products...
  ✓ Created 3 products: HP, HP Act, Leasing

2. Creating Customers...
  ✓ Created 10 customers (7 individuals + 3 companies)

3. Creating Assets...
  ✓ Created 7 assets

4. Setting up Finance Terms...
  ✓ Created/verified 5 terms

5. Creating Contracts with Different Scenarios...
  Scenario 1: Active Individual Contract with Guarantors
    ✓ Created: FC/2024/0001
  Scenario 2: Active Company Contract
    ✓ Created: FC/2024/0002
  Scenario 3: HP Act Contract (Under $55k)
    ✓ Created: FC/2024/0003
  Scenario 4: Finance Lease
    ✓ Created: FC/2024/0004
  Scenario 5: Premium Customer - Mercedes
    ✓ Created: FC/2024/0005
  Scenario 6: Draft Contract (Pending Approval)
    ✓ Created: FC/2024/0006 (Draft)

  ✓ Created 6 contracts covering different scenarios

6. Simulating Payment Scenarios...
  ✓ C1 (FC/2024/0001): 1 on-time payment recorded
  ✓ C2 (FC/2024/0002): 2 payments (1 late, 1 on-time)
  ✓ C5 (FC/2024/0005): 3 on-time payments (good payer)

  ✓ Payment scenarios simulated

==============================================================
TEST DATA SETUP COMPLETE!
==============================================================

📊 Summary:
  • Products: 3 (HP, HP Act, Leasing)
  • Customers: 10 (7 individuals + 3 companies)
  • Assets: 7 vehicles
  • Finance Terms: 5 options (12-60 months)
  • Contracts: 6
    - FC/2024/0001: Active with Guarantors (draft)
    - FC/2024/0002: Company Customer (draft)
    - FC/2024/0003: HP Act (draft)
    - FC/2024/0004: Leasing (draft)
    - FC/2024/0005: Premium Customer (draft)
    - FC/2024/0006: Draft Contract (draft)

✅ Test Scenarios Covered:
  1. Individual customer with guarantors
  2. Company customer
  3. HP Act (under $55k)
  4. Finance lease
  5. Premium customer with large loan
  6. Draft contract (pending)
  7. On-time payments
  8. Late payments
  9. Partial payment history

🧪 Ready to Test:
  • Contract creation and activation
  • Schedule generation (Rule78 & Flat)
  • Payment processing and allocation
  • Overdue detection and penalties
  • Settlement calculations
  • Dashboard KPIs
  • Aging analysis
  • Reporting

============================================================
==================================================
Script execution completed!
==================================================
```

---

## Troubleshooting

### Still Getting company_id Error?

If you still see the error after the fix, check if the script file was properly updated:

```bash
# Verify the fix is in place
grep -A 5 "def get_or_create_account" testing/scripts/setup_test_data_02_enhanced.py

# Should show the try-except version
```

### No Sales/Bank Journal Error?

Create journals via Odoo UI or shell:

```bash
docker-compose exec web ./odoo-bin shell -c /etc/odoo/odoo.conf -d vfs --db_host=db
```

Then in the Python shell:
```python
# Create Sales Journal
env['account.journal'].create({
    'name': 'Sales Journal',
    'type': 'sale',
    'code': 'SAL'
})

# Create Bank Journal
env['account.journal'].create({
    'name': 'Bank',
    'type': 'bank',
    'code': 'BNK1'
})

# Commit
env.cr.commit()
```

### Missing Accounts Error?

Install a Chart of Accounts:
- Login to Odoo web interface
- Settings > Accounting > Fiscal Localization
- Select your country (e.g., Singapore, United States, Generic)
- Click "Apply" or "Install"

---

## After Successful Run

1. **Check Dashboard:**
   ```
   Finance > Dashboard
   ```
   Should show:
   - 5 Active contracts (C6 is draft)
   - Portfolio values
   - Payment data

2. **View Contracts:**
   ```
   Finance > Contracts
   ```
   - 6 contracts total
   - Various states and scenarios

3. **Check Payment History:**
   - Open contracts C1, C2, or C5
   - Go to Schedule tab
   - See payment status

4. **Verify Customers:**
   ```
   Finance > Customers
   ```
   - 10 partners created
   - 7 individuals, 3 companies

---

## File Locations

- **Script:** `testing/scripts/setup_test_data_02_enhanced.py`
- **Runner:** `run_test_data.sh`
- **This guide:** `testing/UBUNTU_RUN_GUIDE.md`
- **General guide:** `testing/HOW_TO_RUN_SCRIPTS.md`
