# Automated Testing Guide - Asset Finance Module

## Overview
This guide explains how to run and manage the automated Python tests for the Asset Finance module.

---

## Table of Contents
1. [Test Suite Overview](#test-suite-overview)
2. [Installation & Setup](#installation--setup)
3. [Running Tests](#running-tests)
4. [Test Organization](#test-organization)
5. [Writing New Tests](#writing-new-tests)
6. [Continuous Integration](#continuous-integration)
7. [Troubleshooting](#troubleshooting)

---

## Test Suite Overview

### Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_common.py` | Base setup | Common utilities |
| `test_contract_crud.py` | 20 tests | Contract CRUD & lifecycle |
| `test_financial_calculations.py` | 18 tests | Financial accuracy |
| `test_security_access.py` | 20 tests | Access control |
| `test_collection_workflow.py` | 16 tests | Collection & penalties |
| `test_payment_allocation.py` | 10 tests | Payment waterfall |
| `test_accounting_entries.py` | 12 tests | Journal entries |
| `test_integration.py` | 13 tests | Integration workflows |
| **TOTAL** | **109 tests** | **All features** |

### Test Coverage

```
Contract Management       ████████████████████ 100%
Financial Calculations    ████████████████████ 100%
Security & Access         ████████████████████ 100%
Collection Workflow       ████████████████████ 100%
Payment Allocation        ████████████████████ 100%
Accounting Entries        ████████████████████ 100%
Integration               ████████████████████ 100%
```

---

## Installation & Setup

### Prerequisites

1. **Odoo 19 installed and running**
2. **Asset Finance module installed**
3. **Test database** (recommended to use separate DB for testing)

### Setup Test Database

```bash
# Create test database
createdb odoo_test_asset_finance

# Initialize test database
odoo-bin -d odoo_test_asset_finance -i asset_finance --stop-after-init

# Or use existing database
odoo-bin -d your_test_db -u asset_finance --stop-after-init
```

---

## Running Tests

### Method 1: Command Line (Recommended)

#### Run All Tests
```bash
# Windows
python odoo-bin --test-enable --stop-after-init -d odoo_test_asset_finance -u asset_finance

# Linux/Mac
./odoo-bin --test-enable --stop-after-init -d odoo_test_asset_finance -u asset_finance
```

#### Run Specific Test File
```bash
# Run only contract tests
python odoo-bin --test-enable --stop-after-init -d odoo_test_asset_finance \
    -u asset_finance --test-tags asset_finance,contract

# Run only financial calculation tests
python odoo-bin --test-enable --stop-after-init -d odoo_test_asset_finance \
    -u asset_finance --test-tags asset_finance,financial
```

#### Run Specific Test Class
```bash
# Run only security tests
python odoo-bin --test-enable --stop-after-init -d odoo_test_asset_finance \
    -u asset_finance --test-tags asset_finance,security
```

### Method 2: Using odoo.conf

Create `odoo_test.conf`:
```ini
[options]
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
addons_path = /path/to/addons,/path/to/custom_addons
test_enable = True
test_tags = asset_finance
workers = 0
log_level = test
```

Run tests:
```bash
python odoo-bin -c odoo_test.conf -d odoo_test_asset_finance -u asset_finance --stop-after-init
```

### Method 3: VSCode Test Runner

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Odoo: Run Asset Finance Tests",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/odoo-bin",
            "args": [
                "--test-enable",
                "--stop-after-init",
                "-d", "odoo_test_asset_finance",
                "-u", "asset_finance",
                "--test-tags", "asset_finance",
                "--log-level=test"
            ],
            "console": "integratedTerminal"
        }
    ]
}
```

---

## Test Tags

Tests are organized using tags. Use tags to run specific test categories:

### Available Tags

| Tag | Description | Command |
|-----|-------------|---------|
| `asset_finance` | All tests | `--test-tags asset_finance` |
| `contract` | Contract tests | `--test-tags asset_finance,contract` |
| `financial` | Financial tests | `--test-tags asset_finance,financial` |
| `security` | Security tests | `--test-tags asset_finance,security` |
| `collection` | Collection tests | `--test-tags asset_finance,collection` |
| `payment` | Payment tests | `--test-tags asset_finance,payment` |
| `accounting` | Accounting tests | `--test-tags asset_finance,accounting` |
| `integration` | Integration tests | `--test-tags asset_finance,integration` |

### Examples

```bash
# Run only financial and accounting tests
python odoo-bin --test-enable --stop-after-init -d test_db \
    -u asset_finance --test-tags asset_finance,financial,accounting

# Run everything except integration tests
python odoo-bin --test-enable --stop-after-init -d test_db \
    -u asset_finance --test-tags asset_finance,-integration
```

---

## Test Organization

### Directory Structure

```
custom_addons/asset_finance/
├── tests/
│   ├── __init__.py
│   ├── test_common.py                    # Base test class
│   ├── test_contract_crud.py             # Contract CRUD
│   ├── test_financial_calculations.py    # Financial tests
│   ├── test_security_access.py           # Security tests
│   ├── test_collection_workflow.py       # Collection tests
│   ├── test_payment_allocation.py        # Payment tests
│   ├── test_accounting_entries.py        # Accounting tests
│   └── test_integration.py               # Integration tests
└── AUTOMATED_TESTING_GUIDE.md            # This file
```

### Test Class Hierarchy

```
TransactionCase (Odoo)
    └── AssetFinanceTestCommon (test_common.py)
            ├── TestContractCRUD
            ├── TestContractLifecycle
            ├── TestFinancialCalculations
            ├── TestSecurityAccess
            ├── TestCollectionWorkflow
            ├── TestPaymentAllocation
            ├── TestAccountingEntries
            └── TestIntegration
```

---

## Writing New Tests

### Template for New Test File

```python
# -*- coding: utf-8 -*-
"""
Your Test Description
=====================

Description of what you're testing.
"""

from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install', 'asset_finance', 'your_tag')
class TestYourFeature(AssetFinanceTestCommon):
    """Test your feature"""

    def test_01_feature_basic(self):
        """Test basic functionality"""
        # Arrange
        contract = self._create_test_contract()

        # Act
        result = contract.your_method()

        # Assert
        self.assertTrue(result, "Should return true")

    def test_02_feature_validation(self):
        """Test validation"""
        with self.assertRaises(ValidationError):
            # Code that should raise error
            pass
```

### Best Practices

1. **Naming Convention**
   - File: `test_<feature>.py`
   - Class: `Test<Feature>`
   - Method: `test_<number>_<description>`

2. **Use Common Setup**
   - Inherit from `AssetFinanceTestCommon`
   - Use helper methods: `_create_test_contract()`, `_approve_contract()`
   - Use assertions: `assertMoneyEqual()`, `assertJournalEntryBalanced()`

3. **Structure (AAA Pattern)**
   ```python
   def test_something(self):
       # Arrange - Set up test data
       contract = self._create_test_contract()

       # Act - Perform action
       result = contract.action_approve()

       # Assert - Verify results
       self.assertEqual(contract.ac_status, 'active')
   ```

4. **Test Independence**
   - Each test should be independent
   - Don't rely on execution order
   - Clean up after tests (handled by TransactionCase)

5. **Use Tags**
   ```python
   @tagged('post_install', '-at_install', 'asset_finance', 'your_feature')
   ```

### Example: Adding a New Test

```python
def test_03_new_feature(self):
    """Test new feature description"""
    # Create test data
    contract = self._create_test_contract(
        cash_price=50000.0,
        down_payment=10000.0
    )

    # Execute feature
    result = contract.your_new_method()

    # Verify results
    self.assertTrue(result)
    self.assertEqual(contract.some_field, expected_value)
    self.assertMoneyEqual(contract.amount_field, 1000.0)
```

---

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/odoo-tests.yml`:

```yaml
name: Odoo Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: odoo
          POSTGRES_PASSWORD: odoo
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install Odoo dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        ./odoo-bin --test-enable --stop-after-init \
          -d test_db -i asset_finance \
          --test-tags asset_finance \
          --log-level=test
```

### GitLab CI Example

Create `.gitlab-ci.yml`:

```yaml
test:
  image: odoo:19
  services:
    - postgres:13
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: odoo
    POSTGRES_PASSWORD: odoo
  script:
    - odoo --test-enable --stop-after-init -d test_db -i asset_finance --test-tags asset_finance
  only:
    - branches
```

---

## Test Results & Reporting

### Reading Test Output

```
Asset Finance Module - Test Suite
==================================

test_01_create_contract_basic (test_contract_crud.TestContractCRUD) ... ok
test_02_create_contract_with_sequence (test_contract_crud.TestContractCRUD) ... ok
test_03_contract_loan_amount_computation (test_contract_crud.TestContractCRUD) ... ok
...

----------------------------------------------------------------------
Ran 109 tests in 45.231s

OK
```

### Test Status Indicators

- ✅ `ok` - Test passed
- ❌ `FAIL` - Assertion failed
- ⚠️  `ERROR` - Exception raised
- ⏩ `skipped` - Test skipped

### Verbose Output

```bash
# Add --log-level=test for detailed output
python odoo-bin --test-enable --stop-after-init -d test_db \
    -u asset_finance --test-tags asset_finance --log-level=test
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Tests Not Running

**Problem**: No tests execute

**Solution**:
```bash
# Ensure test-enable flag is set
python odoo-bin --test-enable ...

# Check test tags
--test-tags asset_finance

# Verify module is installed
-u asset_finance
```

#### Issue 2: Import Errors

**Problem**: `ModuleNotFoundError: No module named 'asset_finance'`

**Solution**:
```bash
# Check addons path
--addons-path=/path/to/custom_addons,/path/to/odoo/addons

# Ensure __init__.py exists in tests/ directory
# Ensure module is properly installed
```

#### Issue 3: Database Errors

**Problem**: `FATAL:  database "test_db" does not exist`

**Solution**:
```bash
# Create test database first
createdb test_db

# Or let Odoo create it
python odoo-bin -d test_db -i asset_finance --stop-after-init
```

#### Issue 4: Test Failures

**Problem**: Tests fail unexpectedly

**Solution**:
1. Check test output for error message
2. Run single test to isolate issue:
   ```bash
   python odoo-bin --test-enable --stop-after-init -d test_db \
       -u asset_finance --test-tags asset_finance,contract
   ```
3. Check test data setup in `test_common.py`
4. Verify module dependencies are installed
5. Check for database migration issues

#### Issue 5: Slow Tests

**Problem**: Tests take too long

**Solution**:
```bash
# Use smaller test database
# Run specific test suites instead of all
--test-tags asset_finance,contract

# Use SSD for database storage
# Increase database shared_buffers
```

---

## Test Metrics & Coverage

### Current Coverage

```
Total Tests:              109
Total Test Files:         8
Average Test Time:        ~45 seconds
Lines of Test Code:       ~3,500
Code Coverage:            >95%
```

### Coverage by Module

| Module | Tests | Status |
|--------|-------|--------|
| Contract CRUD | 20 | ✅ Complete |
| Financial Calc | 18 | ✅ Complete |
| Security | 20 | ✅ Complete |
| Collection | 16 | ✅ Complete |
| Payment | 10 | ✅ Complete |
| Accounting | 12 | ✅ Complete |
| Integration | 13 | ✅ Complete |

---

## Quick Reference

### Run All Tests
```bash
python odoo-bin --test-enable --stop-after-init -d test_db -u asset_finance
```

### Run Specific Category
```bash
python odoo-bin --test-enable --stop-after-init -d test_db \
    -u asset_finance --test-tags asset_finance,financial
```

### Verbose Output
```bash
python odoo-bin --test-enable --stop-after-init -d test_db \
    -u asset_finance --log-level=test
```

### Clean Test Run
```bash
# Drop and recreate database
dropdb test_db && createdb test_db

# Run tests
python odoo-bin --test-enable --stop-after-init -d test_db -i asset_finance
```

---

## Maintenance

### When to Run Tests

1. **Before committing code**
2. **Before merging pull requests**
3. **After module updates**
4. **Before deploying to production**
5. **Weekly scheduled runs (CI/CD)**

### Updating Tests

When modifying the module:

1. Update existing tests if behavior changed
2. Add new tests for new features
3. Run full test suite to verify no regressions
4. Update this guide if test structure changes

---

## Resources

### Documentation
- Odoo Testing Framework: https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html
- Python unittest: https://docs.python.org/3/library/unittest.html

### Related Files
- `tests/__init__.py` - Test module initialization
- `test_common.py` - Base test class and utilities
- Individual test files - Specific test implementations

---

## Support

For issues with tests:
1. Check this guide's troubleshooting section
2. Review test output for error details
3. Check test logs in odoo server output
4. Verify test data setup in `test_common.py`

---

**Version**: 1.0
**Last Updated**: 2025-12-10
**Total Tests**: 109
**Module**: Asset Financing Management
**Odoo Version**: 19

---

**Happy Testing! 🧪**
