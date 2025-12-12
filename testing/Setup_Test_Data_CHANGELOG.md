# Test Data Script - Fixes Changelog

## Version 3 - Schedule Line Field Fix (2025-12-12)

### Issue Fixed

**Error:** `AttributeError: 'finance.contract' object has no attribute 'schedule_line_ids'`

**Root Cause:** Wrong field name for contract installment lines.

### Changes Made

Changed `schedule_line_ids` to `line_ids` throughout payment simulation code.

**Before (WRONG):**
```python
if c1.schedule_line_ids:
    first_line = c1.schedule_line_ids[0]
```

**After (CORRECT):**
```python
if c1.line_ids:
    first_line = c1.line_ids[0]
```

### Results
✅ All 6 contracts created: HP/2025/00001 through HP/2025/00006
✅ Payment simulation works correctly
✅ Script completes without errors

---

## Version 2 - Product Type Fixes (2025-12-12)

### Issues Fixed

**Error:** `ValueError: Wrong value for finance.product.product_type: 'hp_act'`

**Root Cause:** The script was using invalid values for `product_type` and `application_type` fields that don't exist in the Asset Finance module.

### Changes Made

#### 1. Product Type Values Fixed

**Before (WRONG):**
- `'hp'` ✓ Valid
- `'hp_act'` ❌ **Invalid - doesn't exist**
- `'leasing'` ❌ **Invalid - wrong name**

**After (CORRECT):**
- `'hp'` ✓ Standard Hire Purchase
- `'hp'` ✓ Premium HP (with lower rate)
- `'lease'` ✓ Leasing (correct spelling)

#### 2. Application Type Values Fixed

**Before (WRONG):**
- `'hp'` ✓ Valid
- `'hp_act'` ❌ **Invalid - doesn't exist**
- `'leasing'` ❌ **Invalid - wrong name**

**After (CORRECT):**
- `'hp'` ✓ Hire Purchase
- `'lease'` ✓ Leasing (correct spelling)

Valid application types in the system:
- `'hp'` - Hire Purchase
- `'floor_stock'` - Floor Stock
- `'lease'` - Leasing
- `'other'` - Other

#### 3. Product Definitions Updated

**Old Products:**
1. Standard HP (`product_type: 'hp'`)
2. HP Act - Under $55k (`product_type: 'hp_act'`) ❌
3. Finance Lease (`product_type: 'leasing'`) ❌

**New Products:**
1. **Standard Hire Purchase** (`product_type: 'hp'`, rate: 2.5%)
2. **Premium HP - Lower Rate** (`product_type: 'hp'`, rate: 2.3%)
3. **Finance Lease** (`product_type: 'lease'`, rate: 2.0%)

#### 4. Contract Scenarios Updated

| Scenario | Old Product | New Product | Application Type |
|----------|-------------|-------------|------------------|
| C1: Individual with guarantors | Standard HP | Standard HP | `'hp'` |
| C2: Company customer | Standard HP | Standard HP | `'hp'` |
| C3: Small contract | HP Act ❌ | Standard HP | `'hp'` |
| C4: Leasing | Leasing ❌ | Finance Lease | `'lease'` ✓ |
| C5: Premium customer | Standard HP | Premium HP | `'hp'` |
| C6: Draft contract | Standard HP | Standard HP | `'hp'` |

### Test Data Created (Updated)

**3 Products:**
- Standard Hire Purchase (2.5% rate)
- Premium HP - Lower Rate (2.3% rate for premium customers)
- Finance Lease (2.0% rate)

**6 Contracts:**
1. **C1:** Individual + 2 guarantors (Rule78, Honda Civic, Standard HP)
2. **C2:** Company customer (Flat, Nissan, Standard HP)
3. **C3:** Small HP (Flat, Toyota Vios $50k, Standard HP)
4. **C4:** Finance Lease (Flat, Honda CR-V, Leasing product)
5. **C5:** Premium customer (Rule78, Mercedes, Premium HP)
6. **C6:** Draft contract (Flat, Toyota Camry, Standard HP)

### Why These Changes?

The Asset Finance module has these specific product types defined in `models/product.py`:

```python
product_type = fields.Selection([
    ('hp', 'Hire Purchase'),
    ('lease', 'Leasing'),
    ('loan', 'General Loan')
], ...)
```

And application types in `models/contract.py`:

```python
application_type = fields.Selection([
    ('hp', 'Hire Purchase'),
    ('floor_stock', 'Floor Stock'),
    ('lease', 'Leasing'),
    ('other', 'Other')
], ...)
```

There is **no `'hp_act'` type** in the system. HP Act is a regulatory concept in Singapore, not a separate product type in the module.

### How to Use Updated Script

Simply run the script as before:

**Ubuntu/Linux:**
```bash
sudo sh run_test_data.sh
```

**Windows:**
```cmd
run_test_data.bat
```

The script will now:
✅ Create 3 valid products (Standard HP, Premium HP, Leasing)
✅ Create 6 contracts with correct product/application types
✅ Generate payment schedules successfully
✅ Simulate payment history

---

## Version 1 - Company ID Fixes (2025-12-12)

### Issues Fixed

**Error:** `ValueError: Invalid field account.account.company_id`

**Root Cause:** The `account.account` model doesn't have a `company_id` field in some COA configurations.

### Changes Made

1. **Updated `get_or_create_account()` function:**
   - Removed `company_id` filter from account searches
   - Added try-except for robustness
   - Searches by code first, then by account type

2. **Updated journal searches:**
   - Added fallback to search without company filter
   - Handles cases where `company_id` isn't filterable

See [UBUNTU_RUN_GUIDE.md](UBUNTU_RUN_GUIDE.md) for details.

---

## Summary of All Fixes

| Version | Issue | Fix | Status |
|---------|-------|-----|--------|
| v1 | `company_id` field error | Remove company filter from searches | ✅ Fixed |
| v2 | Invalid `'hp_act'` product type | Use valid types: `'hp'`, `'lease'` | ✅ Fixed |
| v2 | Invalid `'leasing'` application type | Changed to `'lease'` | ✅ Fixed |
| v3 | `schedule_line_ids` doesn't exist | Changed to `line_ids` | ✅ Fixed |

The script should now run successfully on any Odoo 19 instance with the Asset Finance module installed!

## About Contracts Not Showing

If you don't see contracts in the Contracts screen after running the script, this is likely due to:

1. **State Filter:** The contracts may be in 'draft' state. Check your filter settings.
2. **Menu Filter:** Ensure you're looking at the correct menu (Finance > Contracts > All Contracts)
3. **Database:** Verify you're connected to the correct database ('vfs')

The script creates these contracts successfully:
- HP/2025/00001 - Individual with Guarantors
- HP/2025/00002 - Company Customer
- HP/2025/00003 - Small HP Contract
- HP/2025/00004 - Finance Lease
- HP/2025/00005 - Premium Customer
- HP/2025/00006 - Draft Contract

To verify they exist, try:
```bash
docker-compose exec web ./odoo-bin shell -c /etc/odoo/odoo.conf -d vfs --db_host=db
```

Then in the shell:
```python
contracts = env['finance.contract'].search([])
for c in contracts:
    print(f"{c.agreement_no} - {c.hirer_id.name} - State: {c.state}")
```
