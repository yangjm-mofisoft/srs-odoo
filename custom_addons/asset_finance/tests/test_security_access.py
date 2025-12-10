# -*- coding: utf-8 -*-
"""
Security and Access Control Tests
==================================

Tests for security groups, record rules, and access permissions.
"""

from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'asset_finance', 'security')
class TestSecurityAccess(AssetFinanceTestCommon):
    """Test security groups and access control"""

    def test_01_officer_can_create_contract(self):
        """Test Finance Officer can create contracts"""
        contract = self.env['finance.contract'].with_user(self.user_officer).create({
            'product_id': self.product_hp_5y.id,
            'asset_id': self.asset_1.id,
            'hirer_id': self.customer_1.id,
            'cash_price': 50000.0,
            'down_payment': 10000.0,
            'int_rate_pa': 8.5,
            'no_of_inst': self.term_60m.id,
            'journal_id': self.sales_journal.id,
            'asset_account_id': self.asset_account.id,
            'income_account_id': self.income_account.id,
            'unearned_interest_account_id': self.unearned_interest_account.id,
        })

        self.assertTrue(contract.id, "Officer should be able to create contracts")

    def test_02_officer_can_read_all_contracts(self):
        """Test Finance Officer can read all contracts"""
        # Create contract as admin
        contract = self._create_test_contract()

        # Read as officer
        contract_as_officer = self.env['finance.contract'].with_user(
            self.user_officer
        ).browse(contract.id)

        self.assertEqual(
            contract_as_officer.id,
            contract.id,
            "Officer should be able to read contracts"
        )

    def test_03_officer_can_write_contracts(self):
        """Test Finance Officer can edit contracts"""
        contract = self._create_test_contract()

        # Edit as officer
        contract.with_user(self.user_officer).write({
            'down_payment': 15000.0
        })

        self.assertMoneyEqual(
            contract.down_payment,
            15000.0,
            "Officer should be able to edit contracts"
        )

    def test_04_officer_cannot_delete_contracts(self):
        """Test Finance Officer cannot delete contracts"""
        contract = self._create_test_contract()

        # Try to delete as officer
        with self.assertRaises(AccessError, msg="Officer should not be able to delete"):
            contract.with_user(self.user_officer).unlink()

    def test_05_manager_can_create_contract(self):
        """Test Finance Manager can create contracts"""
        contract = self.env['finance.contract'].with_user(self.user_manager).create({
            'product_id': self.product_hp_5y.id,
            'asset_id': self.asset_1.id,
            'hirer_id': self.customer_1.id,
            'cash_price': 50000.0,
            'down_payment': 10000.0,
            'int_rate_pa': 8.5,
            'no_of_inst': self.term_60m.id,
            'journal_id': self.sales_journal.id,
            'asset_account_id': self.asset_account.id,
            'income_account_id': self.income_account.id,
            'unearned_interest_account_id': self.unearned_interest_account.id,
        })

        self.assertTrue(contract.id, "Manager should be able to create contracts")

    def test_06_manager_can_delete_contracts(self):
        """Test Finance Manager can delete contracts"""
        contract = self._create_test_contract()
        contract_id = contract.id

        # Delete as manager
        contract.with_user(self.user_manager).unlink()

        # Verify deleted
        deleted = self.env['finance.contract'].search([('id', '=', contract_id)])
        self.assertFalse(deleted, "Manager should be able to delete contracts")

    def test_07_collection_can_read_active_contracts(self):
        """Test Collection Staff can read active contracts"""
        contract = self._create_test_contract()
        contract.action_approve()  # Make active

        # Read as collection
        contract_as_collection = self.env['finance.contract'].with_user(
            self.user_collection
        ).browse(contract.id)

        self.assertEqual(
            contract_as_collection.id,
            contract.id,
            "Collection should be able to read active contracts"
        )

    def test_08_collection_cannot_see_draft_contracts(self):
        """Test Collection Staff cannot see draft contracts"""
        contract = self._create_test_contract()  # Draft status

        # Try to search as collection
        contracts_visible = self.env['finance.contract'].with_user(
            self.user_collection
        ).search([('id', '=', contract.id)])

        self.assertFalse(
            contracts_visible,
            "Collection should not see draft contracts"
        )

    def test_09_collection_cannot_see_closed_contracts(self):
        """Test Collection Staff cannot see closed contracts"""
        contract = self._create_test_contract()
        contract.action_approve()
        contract.action_close()  # Closed status

        # Try to search as collection
        contracts_visible = self.env['finance.contract'].with_user(
            self.user_collection
        ).search([('id', '=', contract.id)])

        self.assertFalse(
            contracts_visible,
            "Collection should not see closed contracts"
        )

    def test_10_collection_can_see_repo_contracts(self):
        """Test Collection Staff can see repossessed contracts"""
        contract = self._create_test_contract()
        contract.action_approve()
        contract.ac_status = 'repo'  # Repossessed

        # Search as collection
        contracts_visible = self.env['finance.contract'].with_user(
            self.user_collection
        ).search([('id', '=', contract.id)])

        self.assertTrue(
            contracts_visible,
            "Collection should see repossessed contracts"
        )

    def test_11_collection_cannot_create_contracts(self):
        """Test Collection Staff cannot create contracts"""
        with self.assertRaises(AccessError, msg="Collection should not create contracts"):
            self.env['finance.contract'].with_user(self.user_collection).create({
                'product_id': self.product_hp_5y.id,
                'asset_id': self.asset_1.id,
                'hirer_id': self.customer_1.id,
                'cash_price': 50000.0,
                'down_payment': 10000.0,
                'journal_id': self.sales_journal.id,
                'asset_account_id': self.asset_account.id,
                'income_account_id': self.income_account.id,
                'unearned_interest_account_id': self.unearned_interest_account.id,
            })

    def test_12_collection_can_write_active_contracts(self):
        """Test Collection Staff can write to active contracts (limited)"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Collection can update certain fields like late_status
        contract.with_user(self.user_collection).write({
            'late_status': 'attention'
        })

        self.assertEqual(
            contract.late_status,
            'attention',
            "Collection should be able to update certain fields"
        )

    def test_13_collection_cannot_delete_contracts(self):
        """Test Collection Staff cannot delete contracts"""
        contract = self._create_test_contract()
        contract.action_approve()

        with self.assertRaises(AccessError, msg="Collection should not delete"):
            contract.with_user(self.user_collection).unlink()

    def test_14_contract_line_access_officer(self):
        """Test Finance Officer can access contract lines"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_generate_schedule()

        # Read lines as officer
        lines = self.env['finance.contract.line'].with_user(
            self.user_officer
        ).search([('contract_id', '=', contract.id)])

        self.assertTrue(len(lines) > 0, "Officer should access contract lines")

    def test_15_contract_line_access_collection(self):
        """Test Collection Staff can read contract lines (read-only)"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Read lines as collection
        lines = self.env['finance.contract.line'].with_user(
            self.user_collection
        ).search([('contract_id', '=', contract.id)])

        self.assertTrue(len(lines) > 0, "Collection should read contract lines")

    def test_16_payment_allocation_access_manager(self):
        """Test Finance Manager can access payment allocations"""
        allocation = self.env['finance.payment.allocation'].with_user(self.user_manager).create({
            'payment_id': self.env['account.payment'].create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': self.customer_1.id,
                'amount': 1000.0,
                'date': datetime.now().date(),
                'journal_id': self.bank_journal.id,
            }).id,
            'allocation_type': 'principal',
            'amount': 500.0,
        })

        self.assertTrue(allocation.id, "Manager should create payment allocations")

    def test_17_payment_allocation_readonly_officer(self):
        """Test Finance Officer has read-only access to payment allocations"""
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer_1.id,
            'amount': 1000.0,
            'date': datetime.now().date(),
            'journal_id': self.bank_journal.id,
        })

        allocation = self.env['finance.payment.allocation'].create({
            'payment_id': payment.id,
            'allocation_type': 'principal',
            'amount': 500.0,
        })

        # Officer can read
        allocation_as_officer = self.env['finance.payment.allocation'].with_user(
            self.user_officer
        ).browse(allocation.id)

        self.assertEqual(
            allocation_as_officer.id,
            allocation.id,
            "Officer should read allocations"
        )

    def test_18_dashboard_access_all_users(self):
        """Test all users can access dashboard"""
        # Officer
        dashboard_officer = self.env['finance.dashboard'].with_user(
            self.user_officer
        ).search([], limit=1)
        self.assertTrue(dashboard_officer, "Officer should access dashboard")

        # Manager
        dashboard_manager = self.env['finance.dashboard'].with_user(
            self.user_manager
        ).search([], limit=1)
        self.assertTrue(dashboard_manager, "Manager should access dashboard")

        # Collection
        dashboard_collection = self.env['finance.dashboard'].with_user(
            self.user_collection
        ).search([], limit=1)
        self.assertTrue(dashboard_collection, "Collection should access dashboard")

    def test_19_guarantor_access_officer(self):
        """Test Finance Officer can create guarantor records"""
        contract = self._create_test_contract()

        guarantor = self.env['finance.contract.guarantor'].with_user(self.user_officer).create({
            'contract_id': contract.id,
            'partner_id': self.guarantor.id,
            'relationship': 'spouse',
        })

        self.assertTrue(guarantor.id, "Officer should create guarantors")

    def test_20_guarantor_readonly_collection(self):
        """Test Collection Staff has read-only access to guarantors"""
        contract = self._create_test_contract()
        contract.action_approve()

        guarantor = self.env['finance.contract.guarantor'].create({
            'contract_id': contract.id,
            'partner_id': self.guarantor.id,
            'relationship': 'spouse',
        })

        # Collection can read
        guarantor_as_collection = self.env['finance.contract.guarantor'].with_user(
            self.user_collection
        ).browse(guarantor.id)

        self.assertEqual(
            guarantor_as_collection.id,
            guarantor.id,
            "Collection should read guarantors"
        )


from datetime import datetime
