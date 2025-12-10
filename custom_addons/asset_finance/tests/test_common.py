# -*- coding: utf-8 -*-
"""
Common Test Setup and Utilities
================================

Base test class with common setup for all Asset Finance tests.
"""

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


@tagged('post_install', '-at_install', 'asset_finance')
class AssetFinanceTestCommon(TransactionCase):
    """
    Base test class for Asset Finance module

    Provides common setup and utility methods for all tests.
    """

    @classmethod
    def setUpClass(cls):
        """Set up common test data"""
        super().setUpClass()

        # Get company and currency
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id

        # Create test users with different access levels
        cls._create_test_users()

        # Create accounting configuration
        cls._create_accounts()
        cls._create_journals()

        # Create master data
        cls._create_finance_products()
        cls._create_finance_terms()
        cls._create_penalty_rules()
        cls._create_charges()

        # Create test partners
        cls._create_test_partners()

        # Create test assets
        cls._create_test_assets()

    @classmethod
    def _create_test_users(cls):
        """Create test users with different security groups"""

        # Get security groups
        group_officer = cls.env.ref('asset_finance.group_finance_officer')
        group_manager = cls.env.ref('asset_finance.group_finance_manager')
        group_collection = cls.env.ref('asset_finance.group_collection_staff')

        # Finance Officer
        cls.user_officer = cls.env['res.users'].create({
            'name': 'Test Finance Officer',
            'login': 'test_officer',
            'email': 'test.officer@test.com',
            'groups_id': [(6, 0, [group_officer.id, cls.env.ref('base.group_user').id])]
        })

        # Finance Manager
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Test Finance Manager',
            'login': 'test_manager',
            'email': 'test.manager@test.com',
            'groups_id': [(6, 0, [group_manager.id, cls.env.ref('base.group_user').id])]
        })

        # Collection Staff
        cls.user_collection = cls.env['res.users'].create({
            'name': 'Test Collection Staff',
            'login': 'test_collection',
            'email': 'test.collection@test.com',
            'groups_id': [(6, 0, [group_collection.id, cls.env.ref('base.group_user').id])]
        })

    @classmethod
    def _create_accounts(cls):
        """Create test chart of accounts"""
        AccountAccount = cls.env['account.account']

        # Get account types
        type_receivable = cls.env.ref('account.data_account_type_receivable')
        type_revenue = cls.env.ref('account.data_account_type_revenue')
        type_liability = cls.env.ref('account.data_account_type_current_liabilities')
        type_liquidity = cls.env.ref('account.data_account_type_liquidity')

        # Asset/Receivable Account
        cls.asset_account = AccountAccount.create({
            'code': 'TEST120000',
            'name': 'Test Finance Asset Receivable',
            'account_type': 'asset_receivable',
            'reconcile': True,
        })

        # Interest Income Account
        cls.income_account = AccountAccount.create({
            'code': 'TEST410000',
            'name': 'Test Interest Income',
            'account_type': 'income',
        })

        # Unearned Interest Account (Liability)
        cls.unearned_interest_account = AccountAccount.create({
            'code': 'TEST240000',
            'name': 'Test Unearned Interest',
            'account_type': 'liability_current',
        })

        # Penalty Income Account
        cls.penalty_account = AccountAccount.create({
            'code': 'TEST420000',
            'name': 'Test Penalty Income',
            'account_type': 'income',
        })

        # Admin Fee Expense
        cls.admin_fee_account = AccountAccount.create({
            'code': 'TEST510000',
            'name': 'Test Admin Fee Expense',
            'account_type': 'expense',
        })

        # Bank Account
        cls.bank_account = AccountAccount.create({
            'code': 'TEST100100',
            'name': 'Test Bank Account',
            'account_type': 'asset_cash',
        })

    @classmethod
    def _create_journals(cls):
        """Create test journals"""
        Journal = cls.env['account.journal']

        # Sales Journal
        cls.sales_journal = Journal.create({
            'name': 'Test Sales Journal',
            'code': 'TSJ',
            'type': 'sale',
        })

        # Bank Journal
        cls.bank_journal = Journal.create({
            'name': 'Test Bank Journal',
            'code': 'TBK',
            'type': 'bank',
            'default_account_id': cls.bank_account.id,
        })

        # General Journal
        cls.general_journal = Journal.create({
            'name': 'Test General Journal',
            'code': 'TGJ',
            'type': 'general',
        })

    @classmethod
    def _create_finance_products(cls):
        """Create test financial products"""
        Product = cls.env['finance.product']

        # HP 5-Year Product
        cls.product_hp_5y = Product.create({
            'name': 'Test HP 5-Year',
            'product_type': 'hp',
            'default_int_rate': 8.5,
            'min_months': 12,
            'max_months': 60,
            'step_months': 12,
            'active': True,
        })

        # Leasing 3-Year Product
        cls.product_leasing_3y = Product.create({
            'name': 'Test Leasing 3-Year',
            'product_type': 'leasing',
            'default_int_rate': 6.5,
            'default_rv_percentage': 30.0,
            'annual_mileage_limit': 15000,
            'min_months': 12,
            'max_months': 36,
            'step_months': 12,
            'active': True,
        })

    @classmethod
    def _create_finance_terms(cls):
        """Create test finance terms"""
        Term = cls.env['finance.term']

        cls.term_12m = Term.create({'name': '12 Months', 'months': 12})
        cls.term_24m = Term.create({'name': '24 Months', 'months': 24})
        cls.term_36m = Term.create({'name': '36 Months', 'months': 36})
        cls.term_48m = Term.create({'name': '48 Months', 'months': 48})
        cls.term_60m = Term.create({'name': '60 Months', 'months': 60})

    @classmethod
    def _create_penalty_rules(cls):
        """Create test penalty rules"""
        Rule = cls.env['finance.penalty.rule']

        # Daily percentage rule
        cls.penalty_rule_daily = Rule.create({
            'name': 'Test Daily 0.05%',
            'method': 'daily_percent',
            'rate': 0.05,
            'grace_period_days': 7,
            'active': True,
        })

        # Fixed one-time rule
        cls.penalty_rule_fixed = Rule.create({
            'name': 'Test Fixed $50',
            'method': 'fixed_one_time',
            'fixed_amount': 50.0,
            'grace_period_days': 7,
            'active': True,
        })

    @classmethod
    def _create_charges(cls):
        """Create test charges"""
        Charge = cls.env['finance.charge']

        cls.admin_fee = Charge.create({
            'name': 'Test Admin Fee',
            'type': 'admin',
            'amount': 150.0,
            'active': True,
        })

        cls.processing_fee = Charge.create({
            'name': 'Test Processing Fee',
            'type': 'other',
            'amount': 100.0,
            'active': True,
        })

    @classmethod
    def _create_test_partners(cls):
        """Create test partners"""
        Partner = cls.env['res.partner']

        # Customer 1
        cls.customer_1 = Partner.create({
            'name': 'Test Customer 1',
            'email': 'customer1@test.com',
            'phone': '+65 1234 5678',
            'vat': 'S1234567A',
            'is_company': False,
            'customer_rank': 1,
            'is_finance_customer': True,
        })

        # Customer 2
        cls.customer_2 = Partner.create({
            'name': 'Test Customer 2',
            'email': 'customer2@test.com',
            'phone': '+65 8765 4321',
            'vat': 'S7654321B',
            'is_company': False,
            'customer_rank': 1,
            'is_finance_customer': True,
        })

        # Guarantor
        cls.guarantor = Partner.create({
            'name': 'Test Guarantor',
            'email': 'guarantor@test.com',
            'phone': '+65 9999 8888',
            'vat': 'S9999888A',
            'is_finance_guarantor': True,
        })

        # Supplier/Dealer
        cls.supplier = Partner.create({
            'name': 'Test Dealer',
            'email': 'dealer@test.com',
            'is_company': True,
            'supplier_rank': 1,
            'ref': 'DEALER001',
        })

    @classmethod
    def _create_test_assets(cls):
        """Create test assets with vehicles"""
        Vehicle = cls.env['fleet.vehicle']
        Asset = cls.env['finance.asset']

        # Create vehicle brand
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Toyota'
        })

        # Create vehicle model
        model = cls.env['fleet.vehicle.model'].create({
            'brand_id': brand.id,
            'name': 'Test Corolla'
        })

        # Create vehicles
        cls.vehicle_1 = Vehicle.create({
            'name': 'TEST1234A - Toyota Corolla',
            'license_plate': 'TEST1234A',
            'model_id': model.id,
            'model_year': 2023,
        })

        cls.vehicle_2 = Vehicle.create({
            'name': 'TEST5678B - Toyota Corolla',
            'license_plate': 'TEST5678B',
            'model_id': model.id,
            'model_year': 2023,
        })

        # Create finance assets
        cls.asset_1 = Asset.create({
            'vehicle_id': cls.vehicle_1.id,
            'asset_type': 'motor_vehicle',
            'purchase_price': 50000.0,
            'status': 'available',
        })

        cls.asset_2 = Asset.create({
            'vehicle_id': cls.vehicle_2.id,
            'asset_type': 'motor_vehicle',
            'purchase_price': 45000.0,
            'status': 'available',
        })

    def _create_test_contract(self, **kwargs):
        """
        Helper method to create a test contract

        Args:
            **kwargs: Additional fields to override defaults

        Returns:
            finance.contract: Created contract record
        """
        default_vals = {
            'product_id': self.product_hp_5y.id,
            'asset_id': self.asset_1.id,
            'hirer_id': self.customer_1.id,
            'agreement_date': datetime.now().date(),
            'cash_price': 50000.0,
            'down_payment': 10000.0,
            'int_rate_pa': 8.5,
            'no_of_inst': self.term_60m.id,
            'interest_method': 'rule78',
            'payment_scheme': 'arrears',
            'installment_type': 'annuity',
            'journal_id': self.sales_journal.id,
            'asset_account_id': self.asset_account.id,
            'income_account_id': self.income_account.id,
            'unearned_interest_account_id': self.unearned_interest_account.id,
        }

        # Merge with provided kwargs
        default_vals.update(kwargs)

        return self.env['finance.contract'].create(default_vals)

    def _approve_contract(self, contract):
        """Helper to approve a contract"""
        contract.action_approve()
        self.assertEqual(contract.ac_status, 'active', "Contract should be active after approval")

    def _generate_schedule(self, contract):
        """Helper to generate contract schedule"""
        contract.action_generate_schedule()
        self.assertTrue(len(contract.line_ids) > 0, "Schedule should have installment lines")

    def assertMoneyEqual(self, amount1, amount2, msg=None, delta=0.01):
        """
        Assert two monetary amounts are equal within delta

        Args:
            amount1: First amount
            amount2: Second amount
            msg: Optional message
            delta: Acceptable difference (default 0.01 = 1 cent)
        """
        if msg is None:
            msg = f"Expected {amount1:.2f} to equal {amount2:.2f}"
        self.assertAlmostEqual(amount1, amount2, delta=delta, msg=msg)

    def assertJournalEntryBalanced(self, move):
        """
        Assert that a journal entry is balanced (debits = credits)

        Args:
            move: account.move record
        """
        total_debit = sum(move.line_ids.mapped('debit'))
        total_credit = sum(move.line_ids.mapped('credit'))
        self.assertMoneyEqual(
            total_debit,
            total_credit,
            f"Journal entry {move.name} should be balanced"
        )
