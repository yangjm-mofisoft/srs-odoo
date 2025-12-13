# -*- coding: utf-8 -*-
"""
Accounting Entries Tests
=========================

Tests for journal entry creation and accounting integrity.
"""

from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged
from datetime import datetime


@tagged('post_install', '-at_install', 'asset_finance', 'accounting')
class TestAccountingEntries(AssetFinanceTestCommon):
    """Test accounting journal entries"""

    def test_01_disbursement_entry_creation(self):
        """Test disbursement creates journal entry"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Disburse
        disbursement_date = datetime.now().date()
        move = contract.create_disbursement_entry(
            disbursement_date=disbursement_date,
            payment_method_id=self.bank_journal.id
        )

        self.assertTrue(move.id, "Disbursement entry should be created")
        self.assertEqual(move.state, 'posted', "Entry should be posted")

    def test_02_disbursement_entry_balanced(self):
        """Test disbursement entry is balanced"""
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0
        )
        contract.action_approve()

        # Disburse
        move = contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        # Check balanced
        self.assertJournalEntryBalanced(move)

    def test_03_disbursement_entry_accounts(self):
        """Test disbursement entry has correct accounts"""
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0
        )
        contract.action_approve()

        # Disburse
        move = contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        # Check for required accounts
        accounts_used = move.line_ids.mapped('account_id')

        self.assertIn(
            contract.asset_account_id,
            accounts_used,
            "Should debit asset/receivable account"
        )

        self.assertIn(
            contract.unearned_interest_account_id,
            accounts_used,
            "Should credit unearned interest account"
        )

    def test_04_disbursement_prevents_duplicate(self):
        """Test cannot disburse twice"""
        contract = self._create_test_contract()
        contract.action_approve()

        # First disbursement
        contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        # Try second disbursement
        with self.assertRaises(Exception, msg="Should prevent duplicate disbursement"):
            contract.create_disbursement_entry(
                disbursement_date=datetime.now().date(),
                payment_method_id=self.bank_journal.id
            )

    def test_05_disbursement_with_commission(self):
        """Test disbursement with supplier commission"""
        contract = self._create_test_contract(
            supplier_id=self.supplier.id,
            commission=1000.0
        )
        contract.action_approve()

        # Disburse
        move = contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        # Check supplier account credited
        supplier_line = move.line_ids.filtered(
            lambda l: l.partner_id == self.supplier
        )

        self.assertTrue(
            len(supplier_line) > 0,
            "Should have supplier line"
        )

        self.assertMoneyEqual(
            supplier_line[0].credit,
            1000.0,
            "Supplier should be credited commission amount"
        )

    def test_06_disbursement_with_admin_fee(self):
        """Test disbursement with admin fee"""
        # Configure admin fee account
        self.env['ir.config_parameter'].sudo().set_param(
            'asset_finance.admin_fee_account_id',
            self.admin_fee_account.id
        )

        contract = self._create_test_contract(
            admin_fee=150.0
        )
        contract.action_approve()

        # Disburse
        move = contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        # Check admin fee line
        admin_line = move.line_ids.filtered(
            lambda l: l.account_id == self.admin_fee_account
        )

        self.assertTrue(
            len(admin_line) > 0,
            "Should have admin fee line"
        )

        self.assertMoneyEqual(
            admin_line[0].debit,
            150.0,
            "Admin fee should be debited"
        )

    def test_07_settlement_entry_creation(self):
        """Test settlement creates journal entry"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Mark some lines as paid
        for line in contract.line_ids[:12]:
            line.invoice_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': contract.hirer_id.id,
                'invoice_date': line.date_due,
                'payment_state': 'paid',
            })

        # Process settlement
        settlement_date = datetime.now().date()
        move = contract.process_early_settlement(
            settlement_date=settlement_date,
            payment_journal_id=self.bank_journal.id
        )

        self.assertTrue(move.id, "Settlement entry should be created")
        self.assertEqual(move.state, 'posted', "Entry should be posted")

    def test_08_settlement_entry_balanced(self):
        """Test settlement entry is balanced"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Mark some lines as paid
        for line in contract.line_ids[:12]:
            line.invoice_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': contract.hirer_id.id,
                'invoice_date': line.date_due,
                'payment_state': 'paid',
            })

        # Process settlement
        move = contract.process_early_settlement(
            settlement_date=datetime.now().date(),
            payment_journal_id=self.bank_journal.id
        )

        # Check balanced
        self.assertJournalEntryBalanced(move)

    def test_09_settlement_closes_contract(self):
        """Test settlement closes contract"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Process settlement
        contract.process_early_settlement(
            settlement_date=datetime.now().date(),
            payment_journal_id=self.bank_journal.id
        )

        # Contract should be closed
        self.assertEqual(
            contract.ac_status,
            'closed',
            "Contract should be closed after settlement"
        )

    def test_10_disbursement_action_view(self):
        """Test view disbursement action"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Disburse
        contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        # View action
        action = contract.action_view_disbursement()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.payment')
        self.assertEqual(action['res_id'], contract.disbursement_payment_id.id)

    def test_11_disbursement_link_stored(self):
        """Test disbursement move_id is stored on contract"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Disburse
        move = contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        self.assertEqual(
            contract.disbursement_move_id.id,
            move.id,
            "Disbursement move should be linked to contract"
        )

    def test_12_disbursement_activates_contract(self):
        """Test disbursement keeps contract active"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Disburse
        contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        self.assertEqual(
            contract.ac_status,
            'active',
            "Contract should remain active after disbursement"
        )
