# -*- coding: utf-8 -*-
"""
Test User Access Rights for Asset Finance Module

This test file verifies that:
1. Users can be created with correct roles
2. Each role has appropriate access permissions
3. Record rules work correctly for different roles
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'asset_finance')
class TestUserAccess(TransactionCase):
    """Test user access rights for Asset Finance module"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get security groups
        cls.group_finance_manager = cls.env.ref('asset_finance.group_finance_manager')
        cls.group_finance_officer = cls.env.ref('asset_finance.group_finance_officer')
        cls.group_collection_staff = cls.env.ref('asset_finance.group_collection_staff')

        # Create test users
        cls.user_manager = cls._create_test_user(
            'test_manager',
            'Test Manager',
            [cls.group_finance_manager.id]
        )

        cls.user_officer = cls._create_test_user(
            'test_officer',
            'Test Officer',
            [cls.group_finance_officer.id]
        )

        cls.user_collection = cls._create_test_user(
            'test_collection',
            'Test Collection Staff',
            [cls.group_collection_staff.id]
        )

    @classmethod
    def _create_test_user(cls, login, name, group_ids):
        """Helper method to create test users"""
        return cls.env['res.users'].create({
            'name': name,
            'login': login,
            'email': f'{login}@test.com',
            'groups_id': [(6, 0, group_ids)],
            'company_id': cls.env.company.id,
            'company_ids': [(6, 0, [cls.env.company.id])],
        })

    def test_01_user_creation(self):
        """Test that users are created with correct groups"""
        # Finance Manager should have all three groups (due to implied_ids)
        self.assertIn(
            self.group_finance_manager,
            self.user_manager.groups_id,
            "Finance Manager should have Finance Manager group"
        )
        self.assertIn(
            self.group_finance_officer,
            self.user_manager.groups_id,
            "Finance Manager should have Finance Officer group (implied)"
        )

        # Finance Officer should have only Officer group
        self.assertIn(
            self.group_finance_officer,
            self.user_officer.groups_id,
            "Finance Officer should have Finance Officer group"
        )
        self.assertNotIn(
            self.group_finance_manager,
            self.user_officer.groups_id,
            "Finance Officer should NOT have Finance Manager group"
        )

        # Collection Staff should have only Collection group
        self.assertIn(
            self.group_collection_staff,
            self.user_collection.groups_id,
            "Collection Staff should have Collection Staff group"
        )

    def test_02_dashboard_access(self):
        """Test dashboard access for different roles"""
        Dashboard = self.env['finance.dashboard']

        # All users should be able to READ dashboard
        dashboard_manager = Dashboard.with_user(self.user_manager).search([])
        self.assertTrue(dashboard_manager, "Finance Manager should access dashboard")

        dashboard_officer = Dashboard.with_user(self.user_officer).search([])
        self.assertTrue(dashboard_officer, "Finance Officer should access dashboard")

        dashboard_collection = Dashboard.with_user(self.user_collection).search([])
        self.assertTrue(dashboard_collection, "Collection Staff should access dashboard")

    def test_03_contract_create_access(self):
        """Test contract creation permissions"""
        Contract = self.env['finance.contract']

        # Get required related records
        partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com'
        })

        product = self.env['finance.product'].create({
            'name': 'Test Finance Product',
            'interest_rate': 5.0,
        })

        asset = self.env['finance.asset'].create({
            'name': 'Test Asset',
            'description': 'Test Vehicle',
        })

        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Test Sales Journal',
                'code': 'TSJ',
                'type': 'sale',
            })

        # Get chart of accounts
        account_receivable = self.env['account.account'].search([
            ('account_type', '=', 'asset_receivable')
        ], limit=1)
        account_income = self.env['account.account'].search([
            ('account_type', '=', 'income')
        ], limit=1)
        account_liability = self.env['account.account'].search([
            ('account_type', '=', 'liability_current')
        ], limit=1)

        contract_vals = {
            'name': 'Test Contract',
            'partner_id': partner.id,
            'product_id': product.id,
            'asset_id': asset.id,
            'journal_id': journal.id,
            'asset_account_id': account_receivable.id if account_receivable else False,
            'income_account_id': account_income.id if account_income else False,
            'unearned_interest_account_id': account_liability.id if account_liability else False,
            'hire_price': 10000.0,
            'down_payment': 2000.0,
            'tenure_months': 12,
        }

        # Finance Manager can create contracts
        try:
            contract_manager = Contract.with_user(self.user_manager).create(contract_vals.copy())
            self.assertTrue(contract_manager, "Finance Manager should create contracts")
        except AccessError:
            self.fail("Finance Manager should be able to create contracts")

        # Finance Officer can create contracts
        try:
            contract_vals['name'] = 'Test Contract 2'
            contract_officer = Contract.with_user(self.user_officer).create(contract_vals.copy())
            self.assertTrue(contract_officer, "Finance Officer should create contracts")
        except AccessError:
            self.fail("Finance Officer should be able to create contracts")

        # Collection Staff CANNOT create contracts
        with self.assertRaises(AccessError, msg="Collection Staff should NOT create contracts"):
            contract_vals['name'] = 'Test Contract 3'
            Contract.with_user(self.user_collection).create(contract_vals.copy())

    def test_04_contract_read_access(self):
        """Test contract read permissions with record rules"""
        Contract = self.env['finance.contract']

        # Create test contracts with different statuses
        partner = self.env['res.partner'].create({'name': 'Test Customer'})
        product = self.env['finance.product'].create({
            'name': 'Test Product',
            'interest_rate': 5.0,
        })
        asset = self.env['finance.asset'].create({'name': 'Test Asset'})
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        account_receivable = self.env['account.account'].search([
            ('account_type', '=', 'asset_receivable')
        ], limit=1)
        account_income = self.env['account.account'].search([
            ('account_type', '=', 'income')
        ], limit=1)
        account_liability = self.env['account.account'].search([
            ('account_type', '=', 'liability_current')
        ], limit=1)

        # Active contract
        active_contract = Contract.create({
            'name': 'Active Contract',
            'partner_id': partner.id,
            'product_id': product.id,
            'asset_id': asset.id,
            'journal_id': journal.id,
            'asset_account_id': account_receivable.id,
            'income_account_id': account_income.id,
            'unearned_interest_account_id': account_liability.id,
            'hire_price': 10000.0,
            'down_payment': 2000.0,
            'tenure_months': 12,
            'ac_status': 'active',
        })

        # Draft contract
        draft_contract = Contract.create({
            'name': 'Draft Contract',
            'partner_id': partner.id,
            'product_id': product.id,
            'asset_id': asset.id,
            'journal_id': journal.id,
            'asset_account_id': account_receivable.id,
            'income_account_id': account_income.id,
            'unearned_interest_account_id': account_liability.id,
            'hire_price': 15000.0,
            'down_payment': 3000.0,
            'tenure_months': 24,
            'ac_status': 'draft',
        })

        # Finance Manager can see all contracts
        manager_contracts = Contract.with_user(self.user_manager).search([
            ('id', 'in', [active_contract.id, draft_contract.id])
        ])
        self.assertEqual(
            len(manager_contracts), 2,
            "Finance Manager should see all contracts"
        )

        # Finance Officer can see all contracts
        officer_contracts = Contract.with_user(self.user_officer).search([
            ('id', 'in', [active_contract.id, draft_contract.id])
        ])
        self.assertEqual(
            len(officer_contracts), 2,
            "Finance Officer should see all contracts"
        )

        # Collection Staff can only see active/repo contracts (not draft)
        collection_contracts = Contract.with_user(self.user_collection).search([
            ('id', 'in', [active_contract.id, draft_contract.id])
        ])
        self.assertEqual(
            len(collection_contracts), 1,
            "Collection Staff should only see active/repo contracts"
        )
        self.assertEqual(
            collection_contracts.id, active_contract.id,
            "Collection Staff should see the active contract"
        )

    def test_05_implied_groups(self):
        """Test that Finance Manager has implied groups"""
        # Finance Manager should have Accounting Manager access
        account_manager_group = self.env.ref('account.group_account_manager')
        self.assertIn(
            account_manager_group,
            self.user_manager.groups_id,
            "Finance Manager should have Accounting Manager access"
        )

        # Finance Officer should have Billing access
        invoice_group = self.env.ref('account.group_account_invoice')
        self.assertIn(
            invoice_group,
            self.user_officer.groups_id,
            "Finance Officer should have Billing access"
        )

    def test_06_contract_delete_access(self):
        """Test contract deletion permissions"""
        Contract = self.env['finance.contract']

        # Create test contract
        partner = self.env['res.partner'].create({'name': 'Test Customer'})
        product = self.env['finance.product'].create({
            'name': 'Test Product',
            'interest_rate': 5.0,
        })
        asset = self.env['finance.asset'].create({'name': 'Test Asset'})
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        account_receivable = self.env['account.account'].search([
            ('account_type', '=', 'asset_receivable')
        ], limit=1)
        account_income = self.env['account.account'].search([
            ('account_type', '=', 'income')
        ], limit=1)
        account_liability = self.env['account.account'].search([
            ('account_type', '=', 'liability_current')
        ], limit=1)

        # Finance Manager CAN delete contracts
        contract = Contract.create({
            'name': 'Contract to Delete',
            'partner_id': partner.id,
            'product_id': product.id,
            'asset_id': asset.id,
            'journal_id': journal.id,
            'asset_account_id': account_receivable.id,
            'income_account_id': account_income.id,
            'unearned_interest_account_id': account_liability.id,
            'hire_price': 10000.0,
            'down_payment': 2000.0,
            'tenure_months': 12,
        })
        try:
            contract.with_user(self.user_manager).unlink()
        except AccessError:
            self.fail("Finance Manager should be able to delete contracts")

        # Collection Staff CANNOT delete contracts
        contract2 = Contract.create({
            'name': 'Contract to Delete 2',
            'partner_id': partner.id,
            'product_id': product.id,
            'asset_id': asset.id,
            'journal_id': journal.id,
            'asset_account_id': account_receivable.id,
            'income_account_id': account_income.id,
            'unearned_interest_account_id': account_liability.id,
            'hire_price': 10000.0,
            'down_payment': 2000.0,
            'tenure_months': 12,
            'ac_status': 'active',
        })
        with self.assertRaises(AccessError, msg="Collection Staff should NOT delete contracts"):
            contract2.with_user(self.user_collection).unlink()
