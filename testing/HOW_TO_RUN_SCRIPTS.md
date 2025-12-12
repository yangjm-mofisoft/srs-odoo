# How to Run Test Data Scripts in Docker

This guide shows you how to run the test data setup scripts in your Dockerized Odoo environment.

## Prerequisites

1. Docker containers must be running:
   ```bash
   docker-compose up -d
   ```

2. Database must exist and Asset Finance module must be installed

## Method 1: Using the Batch File (Windows - Easiest)

From the `odoo-dev` directory, run:

```cmd
run_test_data.bat <database_name>
```

Example:
```cmd
run_test_data.bat odoo
```

If you omit the database name, it defaults to `odoo`.

## Method 2: Using the Shell Script (Linux/Mac/Git Bash)

From the `odoo-dev` directory, run:

```bash
chmod +x run_test_data.sh
./run_test_data.sh <database_name>
```

Example:
```bash
./run_test_data.sh odoo
```

## Method 3: Manual Execution

If the scripts don't work, you can run manually:

```bash
# 1. Copy script to custom_addons (which is mounted in Docker)
cp testing/scripts/setup_test_data_02_enhanced.py custom_addons/

# 2. Execute using Odoo shell
docker-compose exec -T web odoo shell -d <database_name> --no-http < custom_addons/setup_test_data_02_enhanced.py

# 3. Clean up
rm custom_addons/setup_test_data_02_enhanced.py
```

## Method 4: Interactive Shell (For Debugging)

Enter the Odoo shell interactively:

```bash
docker-compose exec web odoo shell -d <database_name>
```

Then inside the shell, run:

```python
# Copy the contents of setup_test_data_02_enhanced.py and paste here
# OR
exec(open('/mnt/extra-addons/setup_test_data_02_enhanced.py').read())
```

## Troubleshooting

### Error: "No Sales Journal found"
Create a Sales Journal in Odoo first:
- Go to Accounting > Configuration > Journals
- Create a new journal with Type = "Sales"

### Error: "No Bank Journal found"
Create a Bank Journal in Odoo first:
- Go to Accounting > Configuration > Journals
- Create a new journal with Type = "Bank"

### Error: "Missing required accounts"
Ensure you have a Chart of Accounts installed:
- Go to Accounting > Configuration > Chart of Accounts
- If empty, install a chart of accounts (e.g., Singapore or Generic)

### Permission Denied on Shell Scripts
Make the script executable:
```bash
chmod +x run_test_data.sh
```

## Expected Output

When successful, you should see:

```
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
  ...

6. Simulating Payment Scenarios...
  ✓ C1 (FC/2024/0001): 1 on-time payment recorded
  ✓ C2 (FC/2024/0002): 2 payments (1 late, 1 on-time)
  ✓ C5 (FC/2024/0005): 3 on-time payments (good payer)

  ✓ Payment scenarios simulated

==============================================================
TEST DATA SETUP COMPLETE!
==============================================================
```

## What Gets Created

- **3 Products:** HP, HP Act, Leasing
- **10 Customers:** 7 individuals + 3 companies
- **7 Assets:** Various vehicles (Toyota, Honda, Nissan, Mercedes, BMW)
- **5 Finance Terms:** 12, 24, 36, 48, 60 months
- **6 Contracts:**
  1. Individual with guarantors (Rule78, 24 months)
  2. Company customer (Flat, 24 months)
  3. HP Act under $55k (Flat, 36 months)
  4. Finance Lease (Flat, 48 months)
  5. Premium customer - Mercedes (Rule78, 60 months)
  6. Draft contract (not activated)
- **Payment History:** Simulated payments with on-time and late scenarios

## After Running the Script

1. Go to Finance > Dashboard to see the KPIs
2. Check Finance > Contracts to view all created contracts
3. View Finance > Customers to see all partners
4. Open any contract to see the payment schedules
5. Check payment history on contracts with recorded payments
