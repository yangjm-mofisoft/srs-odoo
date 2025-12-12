# Finance Account Configuration System

## Overview

The Finance Account Configuration system replaces hardcoded account codes throughout the Asset Finance module with a flexible, configuration-based approach. This allows the system to work with different Chart of Accounts structures across different clients without code modifications.

## Problem Solved

**Before**: The disbursement wizard and other components had hardcoded account code searches:
```python
others_charges_account = self.env['account.account'].search([('code', '=', '2004')], limit=1)
fee_income_account = self.env['account.account'].search([('code', '=', '5002')], limit=1)
gst_account = self.env['account.account'].search([('code', '=', '6004')], limit=1)
```

**Problem**: Different clients may use different account codes for the same functional purpose.

**After**: Uses configuration-based account mapping:
```python
account_config = self.env['finance.account.config'].get_config()
others_charges_account = account_config.hp_charges_account_id
fee_income_account = account_config.processing_fee_income_account_id
gst_account = account_config.gst_output_account_id
```

## Components

### 1. Model: `finance.account.config`
**File**: [models/account_config.py](models/account_config.py)

**Purpose**: Stores account mapping configuration per company.

**Key Fields**:
- **Asset Accounts**:
  - `hp_debtors_account_id` - HP Debtors (Principal + Interest)
  - `unearned_interest_account_id` - Unearned Interest
  - `hp_charges_account_id` - HP Debtors - Other Charges
  - `installment_contra_account_id` - Installment Contra Account

- **Income Accounts**:
  - `interest_income_account_id` - HP Interest Income
  - `processing_fee_income_account_id` - Processing Fee Income
  - `late_charges_income_account_id` - Late Charges Income
  - `early_settlement_income_account_id` - Early Settlement Fee Income

- **Tax Accounts**:
  - `gst_output_account_id` - GST Output Tax

- **Expense Accounts** (Optional):
  - `block_interest_expense_account_id` - Block Discounting Interest
  - `repo_expense_account_id` - Repossession Expenses
  - `bank_charges_account_id` - Bank Charges

**Key Methods**:
- `get_config(company_id=None)` - Retrieves configuration for a company
- `get_account(account_type, company_id=None)` - Gets specific account by functional type
- `action_auto_configure_from_coa()` - Auto-maps accounts based on standard codes

**Constraints**:
- One configuration record per company (SQL constraint)

### 2. Views: Account Configuration UI
**File**: [views/account_config_views.xml](views/account_config_views.xml)

**Features**:
- Form view with grouped account fields
- "Auto-Configure from COA" button for automatic mapping
- Reference guide showing standard account codes
- Tree view for managing multiple company configurations
- Menu: Finance > Configuration > Account Mapping

### 3. Default Data
**File**: [data/account_config_data.xml](data/account_config_data.xml)

**Purpose**: Creates default configuration on module installation, mapping to accounts defined in `account_chart_data.xml`.

### 4. Security
**File**: [security/ir.model.access.csv](security/ir.model.access.csv)

**Access Rights**:
- Finance Officers: Read-only access
- Finance Managers: Full CRUD access

## Usage

### For Administrators

1. **Navigate to Configuration**:
   - Go to: Finance > Configuration > Account Mapping

2. **Option A - Auto-Configure** (Recommended):
   - Click "Auto-Configure from COA" button
   - System searches for accounts with standard codes (2002, 2003, 2004, 5001, 5002, 5003, 5004, 6004, etc.)
   - Automatically maps found accounts to configuration fields

3. **Option B - Manual Configuration**:
   - Select each account from dropdown for each functional type
   - Save the configuration

### For Developers

**Get Account Configuration**:
```python
# Get full configuration object
account_config = self.env['finance.account.config'].get_config()

# Access specific accounts
hp_debtors = account_config.hp_debtors_account_id
unearned_interest = account_config.unearned_interest_account_id
processing_fee_income = account_config.processing_fee_income_account_id
gst_output = account_config.gst_output_account_id
```

**Get Specific Account by Type**:
```python
# Get account by functional type
account = self.env['finance.account.config'].get_account('processing_fee_income')
```

**Error Handling**:
```python
try:
    account_config = self.env['finance.account.config'].get_config()
except UserError:
    raise UserError(
        "Finance Account Configuration not found. "
        "Please configure account mapping under Finance > Configuration > Account Mapping."
    )

# Check if specific account is configured
if not account_config.hp_charges_account_id:
    raise UserError(
        "HP Charges account not configured. "
        "Please configure it under Finance > Configuration > Account Mapping."
    )
```

## Standard Account Code Mapping

The auto-configuration feature searches for these standard codes:

| Functional Type | Standard Code | Account Name |
|----------------|---------------|--------------|
| HP Debtors | 2002 | HP Debtors - Principal + Interest |
| Unearned Interest | 2003 | HP Debtors - Unearned Interest |
| HP Charges | 2004 | HP Debtors - Others Charges |
| Installment Contra | 2005 | HP Debtors - Installment Contra |
| Interest Income | 5001 | HP Interest Income |
| Processing Fee Income | 5002 | HP Processing Fee |
| Late Charges Income | 5003 | HP Late Charges & Interest |
| Early Settlement Income | 5004 | HP Early Settlement Fee |
| GST Output | 6004 | GST Output Tax |
| Block Interest Expense | 6001 | Block Discounting Interest |
| Repo Expense | 6003 | HP Repo Expenses |
| Bank Charges | 8001 | Bank Charges |

## Files Modified

1. **[models/__init__.py](models/__init__.py)**: Added `from . import account_config`
2. **[__manifest__.py](__manifest__.py)**:
   - Added `data/account_config_data.xml` to data files
   - Added `views/account_config_views.xml` to views
3. **[security/ir.model.access.csv](security/ir.model.access.csv)**: Added access rights for `finance.account.config`
4. **[wizard/disbursement_wizard.py](wizard/disbursement_wizard.py)**: Refactored to use configuration system

## Refactored Components

### Disbursement Wizard
**File**: [wizard/disbursement_wizard.py](wizard/disbursement_wizard.py)

**Changes**:
- Removed hardcoded account code searches
- Now retrieves accounts from configuration at runtime
- Added proper error handling for missing configuration
- Lines 61-68: Get configuration
- Lines 93-107: Use `hp_charges_account_id` from config
- Lines 111-123: Use `processing_fee_income_account_id` from config
- Lines 127-139: Use `gst_output_account_id` from config

## Multi-Company Support

The system supports multiple companies:
- Each company has its own configuration record
- `get_config()` automatically uses current company context
- Can specify company: `get_config(company_id=2)`

## Benefits

1. **Flexibility**: Works with any Chart of Accounts structure
2. **Multi-Client**: Different clients can use different account codes
3. **No Code Changes**: Configuration through UI, no code modifications needed
4. **Auto-Configuration**: Quick setup with standard account codes
5. **Clear Error Messages**: Users know exactly what to configure if missing
6. **Multi-Company**: Supports different configurations per company
7. **Maintainability**: Single source of truth for account mappings

## Migration Notes

### For Existing Installations

1. **Upgrade Module**: The new configuration system will be installed automatically
2. **Run Auto-Configure**: Navigate to Finance > Configuration > Account Mapping and click "Auto-Configure from COA"
3. **Verify Mappings**: Check that all accounts are correctly mapped
4. **Test Disbursement**: Create a test disbursement to ensure it works correctly

### For New Installations

The default configuration is created automatically on module installation, mapping to accounts from `account_chart_data.xml`.

## Future Enhancements

Consider extending this pattern to:
- Contract model (if using hardcoded accounts)
- Interest recognition processes
- Settlement wizard
- Payment allocation
- Late charge calculation
- Any other component with hardcoded account codes

## Testing

After installation/upgrade:

1. **Verify Configuration Exists**:
   - Go to Finance > Configuration > Account Mapping
   - Check that all required accounts are mapped

2. **Test Disbursement**:
   - Create a contract with processing fee and GST
   - Run disbursement wizard
   - Verify journal entry uses correct accounts from configuration

3. **Test Auto-Configure**:
   - Create a new company (if multi-company)
   - Run "Auto-Configure from COA"
   - Verify accounts are mapped correctly

## Support

If you encounter issues:
- Ensure account configuration exists for your company
- Check that all required accounts are mapped
- Verify your Chart of Accounts has the necessary account types
- Review error messages for specific missing accounts
