# -*- coding: utf-8 -*-
"""
Asset Finance Module - Test Suite
==================================

This package contains automated tests for the Asset Finance module.

Test Categories:
- Common: Base setup and utilities
- Contract: Contract CRUD and lifecycle
- Financial: Financial calculations
- Security: Access control and permissions
- Collection: Collection workflow
- Payment: Payment allocation
- Accounting: Journal entries
- Integration: Module integration tests
"""

from . import test_common
from . import test_contract_crud
from . import test_financial_calculations
from . import test_security_access
from . import test_collection_workflow
from . import test_payment_allocation
from . import test_accounting_entries
from . import test_integration
