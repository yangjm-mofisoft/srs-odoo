# Asset Finance Module - Automated Tests

## Quick Start

### Run All Tests
```bash
python odoo-bin --test-enable --stop-after-init -d test_db -u asset_finance
```

### Run Specific Tests
```bash
# Financial calculations only
python odoo-bin --test-enable --stop-after-init -d test_db \
    -u asset_finance --test-tags asset_finance,financial
```

---

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_common.py` | Base | Setup & utilities |
| `test_contract_crud.py` | 20 | Contract CRUD |
| `test_financial_calculations.py` | 18 | Financial accuracy |
| `test_security_access.py` | 20 | Access control |
| `test_collection_workflow.py` | 16 | Collection & penalties |
| `test_payment_allocation.py` | 10 | Payment waterfall |
| `test_accounting_entries.py` | 12 | Journal entries |
| `test_integration.py` | 13 | Integration workflows |

**Total: 109 tests**

---

## Documentation

For complete testing guide, see:
- **[../AUTOMATED_TESTING_GUIDE.md](../AUTOMATED_TESTING_GUIDE.md)** - Full documentation
- **[../TEST_SUITE_SUMMARY.md](../TEST_SUITE_SUMMARY.md)** - Overview & statistics

---

## Test Tags

Use tags to run specific test categories:

```bash
--test-tags asset_finance              # All tests
--test-tags asset_finance,contract     # Contract tests
--test-tags asset_finance,financial    # Financial tests
--test-tags asset_finance,security     # Security tests
--test-tags asset_finance,collection   # Collection tests
--test-tags asset_finance,payment      # Payment tests
--test-tags asset_finance,accounting   # Accounting tests
--test-tags asset_finance,integration  # Integration tests
```

---

## Writing New Tests

1. Create test file in this directory
2. Inherit from `AssetFinanceTestCommon`
3. Use `@tagged` decorator
4. Follow naming convention: `test_<number>_<description>`

Example:
```python
from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged

@tagged('post_install', '-at_install', 'asset_finance', 'your_tag')
class TestYourFeature(AssetFinanceTestCommon):
    def test_01_basic_functionality(self):
        contract = self._create_test_contract()
        # Your test code
        self.assertTrue(contract.id)
```

---

## Common Test Utilities

```python
# Available in AssetFinanceTestCommon

# Test Users
self.user_officer
self.user_manager
self.user_collection

# Accounts
self.asset_account
self.income_account
self.bank_account

# Helpers
contract = self._create_test_contract()
self._approve_contract(contract)
self._generate_schedule(contract)

# Assertions
self.assertMoneyEqual(amount1, amount2)
self.assertJournalEntryBalanced(move)
```

---

## Test Execution

Expected output:
```
Ran 109 tests in 45.231s

OK
```

---

## Support

See **[AUTOMATED_TESTING_GUIDE.md](../AUTOMATED_TESTING_GUIDE.md)** for:
- Detailed setup instructions
- Troubleshooting guide
- CI/CD integration
- Writing test examples
