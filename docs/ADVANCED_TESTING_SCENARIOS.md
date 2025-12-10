# Advanced Testing Scenarios - Asset Finance Module

## Overview
This document contains advanced integration and stress testing scenarios for the Asset Finance module beyond basic permission testing.

---

## Table of Contents
1. [Multi-User Concurrent Testing](#multi-user-concurrent-testing)
2. [Financial Accuracy Scenarios](#financial-accuracy-scenarios)
3. [Collection Workflow Testing](#collection-workflow-testing)
4. [Edge Cases & Error Handling](#edge-cases--error-handling)
5. [Performance Testing](#performance-testing)
6. [Accounting Integrity Testing](#accounting-integrity-testing)
7. [Data Migration Scenarios](#data-migration-scenarios)
8. [Integration Testing](#integration-testing)

---

## Multi-User Concurrent Testing

### Scenario 1: Simultaneous Contract Creation
**Purpose**: Test race conditions and locking mechanisms

**Setup**: 3 users logged in simultaneously

**Steps**:
1. **Officer 1**: Start creating contract for Vehicle A
2. **Officer 2**: Simultaneously create contract for Vehicle A
3. **Officer 3**: Create contract for Vehicle B

**Expected Results**:
- ✅ Officers 1 & 2 both succeed (same vehicle, different contracts OK)
- ✅ All 3 contracts get unique agreement numbers
- ✅ No duplicate sequence numbers
- ✅ No database locking errors

**Verify**:
```sql
-- Check for duplicate agreement numbers
SELECT agreement_no, COUNT(*)
FROM finance_contract
GROUP BY agreement_no
HAVING COUNT(*) > 1;
-- Should return 0 rows
```

---

### Scenario 2: Approve-Edit Conflict
**Purpose**: Test concurrent modifications

**Setup**: Manager and Officer on same contract

**Steps**:
1. **Manager**: Open draft contract, click Approve
2. **Officer**: Simultaneously edit same contract (change down payment)
3. **Officer**: Try to save

**Expected Results**:
- ✅ Manager's approval succeeds first
- ❌ Officer gets "Record has been modified" warning
- ✅ Officer must refresh and re-apply changes
- ✅ No data corruption

---

### Scenario 3: Payment Allocation Race
**Purpose**: Test concurrent payment processing

**Setup**: 2 Managers processing payments

**Steps**:
1. Create contract with $1000 outstanding
2. **Manager 1**: Register $600 payment
3. **Manager 2**: Simultaneously register $500 payment
4. Both click "Post" at same time

**Expected Results**:
- ✅ Both payments post successfully
- ✅ Total allocated: $1,100
- ✅ Contract shows overpayment or credit balance
- ✅ Allocation waterfall applied correctly to each

---

## Financial Accuracy Scenarios

### Scenario 4: Rule of 78 vs Flat Rate Comparison
**Purpose**: Verify interest calculation methods

**Test Contract**:
```
Loan Amount: $12,000
Interest Rate: 10% p.a.
Term: 12 months
Total Interest: $1,200
```

**Method 1: Rule of 78**
```
Sum of Digits = 12×13÷2 = 78

Month 1: Interest = $1,200 × (12/78) = $184.62
Month 2: Interest = $1,200 × (11/78) = $169.23
Month 3: Interest = $1,200 × (10/78) = $153.85
...
Month 12: Interest = $1,200 × (1/78) = $15.38
```

**Method 2: Flat Rate**
```
Each Month: Interest = $1,200 ÷ 12 = $100.00
```

**Testing**:
1. Create two identical contracts (A and B)
2. Contract A: Interest Method = "Rule of 78"
3. Contract B: Interest Method = "Flat Rate"
4. Generate schedules for both

**Verify**:
- ✅ Total interest same: $1,200
- ✅ Rule 78: First installment has higher interest
- ✅ Flat Rate: All installments have equal interest
- ✅ Sum of all interest portions equals term charges

---

### Scenario 5: Early Settlement Rebate Calculation
**Purpose**: Verify settlement calculations are accurate

**Test Contract**:
```
Loan Amount: $50,000
Interest Rate: 8% p.a.
Term: 60 months
Monthly Installment: $1,013.82
Total Interest: $10,829
```

**After 24 Payments** (2 years):
- Paid Installments: 24 × $1,013.82 = $24,331.68
- Remaining Installments: 36
- Outstanding Principal: ~$32,000
- Unearned Interest: ~$5,500

**Calculate Settlement**:
1. Settle contract after 24 months
2. System should calculate:
   - Outstanding Principal: ~$32,000
   - Unearned Interest: ~$5,500
   - Rebate Fee (20%): ~$1,100
   - **Settlement Amount**: $32,000 + $1,100 = $33,100

**Verify**:
- ✅ Settlement amount matches manual calculation
- ✅ Rebate percentage applied from settings
- ✅ Penalties added if any
- ✅ Journal entry debits/credits balance

---

### Scenario 6: Annuity vs Level Principal
**Purpose**: Compare installment calculation methods

**Test Contract**:
```
Loan Amount: $100,000
Interest Rate: 6% p.a.
Term: 12 months
```

**Annuity Method** (Equal Total Payments):
```
Monthly Payment = P × [r(1+r)^n] / [(1+r)^n - 1]
r = 6%/12 = 0.5% = 0.005
n = 12

Monthly = $8,606.64 (constant)
Month 1: Interest $500.00, Principal $8,106.64
Month 2: Interest $459.47, Principal $8,147.17
Month 12: Interest $42.79, Principal $8,563.85
```

**Level Principal** (Equal Principal Payments):
```
Principal Each Month = $100,000 / 12 = $8,333.33
Month 1: Principal $8,333.33, Interest $500.00, Total $8,833.33
Month 2: Principal $8,333.33, Interest $458.33, Total $8,791.67
Month 12: Principal $8,333.33, Interest $41.67, Total $8,375.00
```

**Verify**:
- ✅ Annuity: Total payment constant, principal increases
- ✅ Level: Principal constant, total payment decreases
- ✅ Both sum to same total amount

---

## Collection Workflow Testing

### Scenario 7: Automated Collection Escalation
**Purpose**: Test automatic status changes

**Setup**:
1. Create contract with first due date 100 days ago
2. Do NOT make any payments
3. Run scheduled actions

**Day 0-7** (Grace Period):
```
Run: model._cron_calculate_late_interest()
Expected:
- Total Overdue Days: 0
- Late Status: Normal
- No penalties accrued
```

**Day 8-30**:
```
Expected:
- Total Overdue Days: 1-23
- Late Status: Normal
- Penalties start accruing
```

**Day 31-90**:
```
Expected:
- Total Overdue Days: 24-83
- Late Status: Attention (auto-changed)
- Penalties continuing
```

**Day 91+**:
```
Expected:
- Total Overdue Days: 84+
- Late Status: Legal Action (auto-changed)
- Higher priority in collection reports
```

**Verify Cron Job**:
```python
# Run manually to test
self.env['finance.contract']._cron_calculate_late_interest()

# Check contract
contract = self.env['finance.contract'].browse(CONTRACT_ID)
print(f"Overdue Days: {contract.total_overdue_days}")
print(f"Late Status: {contract.late_status}")
print(f"Penalties: {contract.accrued_penalty}")
```

---

### Scenario 8: Email Template Testing
**Purpose**: Verify all email templates render correctly

**Test Each Template**:

**1. Payment Reminder**:
```
Login: Collection Staff
Navigate: Contract → Send Reminder
Verify Email Contains:
- ✅ Hirer name
- ✅ Agreement number
- ✅ Next due date
- ✅ Amount due
- ✅ Payment instructions
- ✅ Professional formatting
```

**2. Overdue Notice**:
```
Test with contract 15 days overdue
Verify Email Contains:
- ✅ Days overdue (15)
- ✅ Outstanding balance
- ✅ Penalty amount
- ✅ Urgent tone
- ✅ Consequences mentioned
```

**3. 4th Schedule (Legal)**:
```
Test with contract 90+ days overdue
Verify Email Contains:
- ✅ Legal language
- ✅ Statutory notice references
- ✅ Final demand wording
- ✅ Asset repossession warning
- ✅ Date sent recorded in contract
```

**4. Settlement Quotation**:
```
Test with active contract
Verify Email Contains:
- ✅ Outstanding principal
- ✅ Settlement amount
- ✅ Valid until date
- ✅ Payment instructions
- ✅ Contact information
```

---

### Scenario 9: Batch Collection Processing
**Purpose**: Test bulk operations

**Setup**: Create 50 contracts with varying overdue statuses

**Batch Operation 1: Mass Reminder**
```
1. Filter: Active + 7 days overdue
2. Select all (50 contracts)
3. Action → Batch Send Reminders
4. Expected:
   - Success count: 48 (2 have no email)
   - Error count: 2
   - Each successful contract logged in chatter
   - Reminder date stamped
```

**Batch Operation 2: Status Update**
```
1. Create Python script to age multiple contracts
2. Run cron job
3. Verify all statuses updated correctly
4. Check dashboard aging buckets updated
```

---

## Edge Cases & Error Handling

### Scenario 10: Zero Interest Contract
**Purpose**: Handle interest-free contracts

**Test Contract**:
```
Loan Amount: $10,000
Interest Rate: 0%
Term: 12 months
```

**Expected**:
- ✅ Monthly Installment: $833.33
- ✅ No interest lines in schedule
- ✅ Invoices only show principal
- ✅ No unearned interest account entries

---

### Scenario 11: Single Installment Contract
**Purpose**: Handle edge case of 1-month term

**Test Contract**:
```
Loan Amount: $5,000
Interest Rate: 10%
Term: 1 month
```

**Expected**:
- ✅ First Inst = Last Inst = $5,041.67
- ✅ Only 1 line in schedule
- ✅ Settlement not applicable
- ✅ Maturity date = First due date

---

### Scenario 12: Overpayment Handling
**Purpose**: Test excess payment allocation

**Setup**:
```
Contract Balance: $1,000
Payment Registered: $1,500
```

**Expected**:
- ✅ Full $1,000 allocated to contract
- ✅ $500 remains as credit/overpayment
- ✅ No error thrown
- ✅ Contract shows paid/overpaid status
- ⚠️ Manual handling for refund/credit note

---

### Scenario 13: Partial Payment Allocation
**Purpose**: Test insufficient payment

**Setup**:
```
Outstanding: $1,000 installment + $200 penalty
Payment: $500
```

**Expected Allocation**:
- $200 → Penalties (cleared)
- $300 → Installment (partial)
- Invoice status: Partial payment
- Remaining: $700 on installment

---

### Scenario 14: Deleted Customer Handling
**Purpose**: Test referential integrity

**Steps**:
1. Create contract with customer
2. Try to delete customer
3. Expected: ❌ Error - "Customer has active contracts"

**Alternative**:
1. Close all contracts
2. Archive customer
3. Expected: ✅ Customer archived, contracts retained

---

### Scenario 15: Negative Amount Validation
**Purpose**: Test input validation

**Test Cases**:
```
1. Down Payment: -1000
   Expected: ❌ ValidationError

2. Interest Rate: -5%
   Expected: ❌ ValidationError

3. Cash Price: 0
   Expected: ⚠️ Warning but allowed (edge case)

4. Down Payment > Cash Price
   Expected: ❌ ValidationError
```

---

## Performance Testing

### Scenario 16: Bulk Contract Creation
**Purpose**: Test performance with large datasets

**Test**:
```python
# Create 1000 contracts
for i in range(1000):
    contract = self.env['finance.contract'].create({
        'product_id': product.id,
        'asset_id': assets[i].id,
        'hirer_id': customers[i % 100].id,
        'cash_price': 50000,
        'down_payment': 10000,
        'int_rate_pa': 8.5,
        'no_of_inst': term_60.id,
    })
    contract.action_generate_schedule()
```

**Measure**:
- Time to create 1000 contracts
- Time to generate schedules
- Database size increase
- Dashboard load time

**Targets**:
- ✅ < 0.5s per contract creation
- ✅ < 1s per schedule generation
- ✅ Dashboard loads < 3s with 1000 active

---

### Scenario 17: Dashboard with Large Portfolio
**Purpose**: Test dashboard performance

**Setup**: 1000 active contracts with varying statuses

**Test**:
1. Navigate to Dashboard
2. Measure load time
3. Click each KPI card (drill-down)
4. Measure response time

**Targets**:
- ✅ Initial load: < 3 seconds
- ✅ KPI drill-down: < 1 second
- ✅ No timeout errors
- ✅ All KPIs calculate correctly

---

### Scenario 18: Report Generation Speed
**Purpose**: Test SQL view performance

**Test Each Report**:
```
1. Aging Report with 1000 contracts
2. Collection Report with 500 overdue
3. Disbursement Report with 100 entries
4. Portfolio Report with 1000 active
```

**Measure**:
- Query execution time
- View render time
- Export to Excel time

**Targets**:
- ✅ Query: < 2 seconds
- ✅ Render: < 3 seconds
- ✅ Export: < 5 seconds

---

## Accounting Integrity Testing

### Scenario 19: Journal Entry Balancing
**Purpose**: Verify all journal entries balance

**Test**:
```sql
-- Check all finance-related journal entries balance
SELECT
    am.id,
    am.ref,
    SUM(aml.debit) as total_debit,
    SUM(aml.credit) as total_credit,
    SUM(aml.debit - aml.credit) as balance
FROM account_move am
JOIN account_move_line aml ON am.id = aml.move_id
WHERE am.ref LIKE '%Disbursement%'
   OR am.ref LIKE '%Settlement%'
   OR am.ref LIKE '%Interest Recognition%'
GROUP BY am.id, am.ref
HAVING SUM(aml.debit - aml.credit) != 0;

-- Should return 0 rows (all balanced)
```

---

### Scenario 20: Interest Recognition Accuracy
**Purpose**: Verify monthly interest recognition

**Setup**: Contract with known interest

**Steps**:
1. Create contract: $10,000 loan, 12 months, $1,200 interest
2. Pay 3 installments
3. Run `_cron_recognize_monthly_interest()`
4. Check unearned interest account

**Expected**:
- Initial unearned: $1,200 (Cr)
- After 3 months: $900 (Cr) remaining
- Income recognized: $300 (Cr)
- Journal entries balance

---

### Scenario 21: Settlement Journal Verification
**Purpose**: Verify settlement accounting

**Test Settlement**:
```
Outstanding Principal: $30,000
Unearned Interest: $5,000
Rebate Fee (20%): $1,000
Penalties: $500

Expected Journal Entry:
Dr. Bank                    31,500
Dr. Unearned Interest        4,000  (5,000 - 1,000)
    Cr. Receivable/Asset    30,000
    Cr. Income (Rebate)      1,000
    Cr. Penalty Account        500

Total Dr: 35,500
Total Cr: 31,500
Balance: 0 ✅
```

---

## Data Migration Scenarios

### Scenario 22: Import Existing Contracts
**Purpose**: Test bulk import functionality

**Prepare CSV**:
```csv
agreement_no,hirer_name,asset_reg,cash_price,down_payment,int_rate,term_months
HP001,John Doe,SXX1234A,50000,10000,8.5,60
HP002,Jane Smith,SXX5678B,40000,8000,7.5,48
```

**Import Process**:
1. Navigate to Contracts
2. Action → Import
3. Upload CSV
4. Map fields
5. Validate data
6. Import

**Verify**:
- ✅ All contracts created
- ✅ Sequences not broken
- ✅ Related records linked correctly
- ✅ No duplicate data

---

### Scenario 23: Export-Modify-Import Cycle
**Purpose**: Test round-trip data handling

**Steps**:
1. Export 100 contracts to CSV
2. Modify interest rates in Excel
3. Re-import (update mode)
4. Verify changes applied

**Expected**:
- ✅ Only modified fields updated
- ✅ No new records created
- ✅ Schedules not regenerated automatically
- ⚠️ User must manually regenerate schedules

---

## Integration Testing

### Scenario 24: Fleet Module Integration
**Purpose**: Test vehicle/asset linking

**Test**:
1. Create vehicle in Fleet module
2. Create contract linked to vehicle
3. Update vehicle details
4. Verify contract shows updated info
5. Try to delete vehicle with active contract

**Expected**:
- ✅ Asset details auto-populate in contract
- ✅ Updates reflect in contract (if related fields)
- ❌ Cannot delete vehicle with active contracts

---

### Scenario 25: Accounting Module Integration
**Purpose**: Test journal entry flow

**Test Full Cycle**:
1. Disburse contract → Check journal entry
2. Create invoices → Check receivable entries
3. Register payment → Check bank/receivable entries
4. Recognize interest → Check income entries
5. Settle early → Check write-off entries

**Verify**:
- ✅ All entries posted automatically
- ✅ Reconciliation works
- ✅ Reports reflect all transactions
- ✅ Trial balance remains balanced

---

### Scenario 26: Multi-Currency (Future)
**Purpose**: Prepare for multi-currency support

**Test**:
1. Contract in USD: $50,000
2. Payment in SGD: S$67,500 (rate: 1.35)
3. Expected: System handles conversion

**Current Status**: Single currency only
**Future Enhancement**: Add currency conversion logic

---

## Stress Testing

### Scenario 27: Maximum Installments
**Purpose**: Test with longest term

**Test**:
```
Loan Amount: $100,000
Term: 120 months (10 years)
Interest Rate: 6%
```

**Expected**:
- ✅ Schedule generates 120 lines
- ✅ No performance degradation
- ✅ List view handles 120 rows
- ✅ Total calculations correct

---

### Scenario 28: High-Value Contract
**Purpose**: Test with large numbers

**Test**:
```
Cash Price: $10,000,000
Down Payment: $2,000,000
Loan Amount: $8,000,000
Interest: $2,400,000
```

**Expected**:
- ✅ No integer overflow
- ✅ Decimal precision maintained
- ✅ Display formatting correct
- ✅ Accounting entries accurate

---

## Regression Testing Checklist

After any code changes, run these tests:

### Core Functionality ✅
- [ ] Contract creation
- [ ] Schedule generation (Rule 78 & Flat)
- [ ] Approval workflow
- [ ] Disbursement entry
- [ ] Invoice generation
- [ ] Payment allocation
- [ ] Penalty calculation
- [ ] Early settlement
- [ ] Email sending

### Security ✅
- [ ] Officer cannot approve
- [ ] Collection cannot create
- [ ] Manager has full access
- [ ] Record rules working

### Calculations ✅
- [ ] Interest calculations match
- [ ] Settlement rebate correct
- [ ] Payment allocation waterfall
- [ ] Penalty accrual accurate

### Integration ✅
- [ ] Dashboard KPIs correct
- [ ] Reports show data
- [ ] Journal entries balance
- [ ] Email templates render

---

## Automated Testing Script

### Python Test Template
```python
# tests/test_contract_calculations.py
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestContractCalculations(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['finance.product'].create({
            'name': 'Test HP Product',
            'product_type': 'hp',
            'default_int_rate': 10.0,
        })

    def test_loan_amount_calculation(self):
        """Test loan amount = cash price - down payment"""
        contract = self.env['finance.contract'].create({
            'product_id': self.product.id,
            'cash_price': 50000,
            'down_payment': 10000,
        })
        self.assertEqual(contract.loan_amount, 40000)

    def test_down_payment_validation(self):
        """Test down payment cannot exceed cash price"""
        with self.assertRaises(ValidationError):
            self.env['finance.contract'].create({
                'product_id': self.product.id,
                'cash_price': 50000,
                'down_payment': 60000,  # Invalid!
            })

    def test_rule_of_78_calculation(self):
        """Test Rule of 78 interest allocation"""
        # TODO: Implement detailed Rule 78 test
        pass
```

---

## Performance Benchmarks

### Target Metrics
| Operation | Target Time | Acceptable | Slow |
|-----------|-------------|------------|------|
| Create Contract | < 0.5s | < 1s | > 2s |
| Generate Schedule (60 months) | < 1s | < 2s | > 3s |
| Dashboard Load | < 2s | < 3s | > 5s |
| Report Query | < 1s | < 2s | > 3s |
| Payment Processing | < 1s | < 2s | > 3s |
| Cron Job (1000 contracts) | < 30s | < 60s | > 120s |

---

## Conclusion

This advanced testing guide ensures:
- ✅ Financial calculations are accurate
- ✅ Concurrent operations work correctly
- ✅ Edge cases are handled
- ✅ Performance meets targets
- ✅ Accounting integrity maintained
- ✅ Integration points work
- ✅ Security boundaries enforced

**Recommended Testing Frequency**:
- Basic tests: Every code change
- Advanced tests: Weekly during development
- Full regression: Before each release
- Performance tests: Monthly in production

---

**Version**: 1.0
**Last Updated**: 2025-12-10
**Module**: Asset Financing Management
