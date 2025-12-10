# -*- coding: utf-8 -*-
"""
Collection Workflow Tests
==========================

Tests for collection management, penalties, and workflow.
"""

from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


@tagged('post_install', '-at_install', 'asset_finance', 'collection')
class TestCollectionWorkflow(AssetFinanceTestCommon):
    """Test collection workflow and penalty calculations"""

    def test_01_overdue_status_computation(self):
        """Test overdue days computation"""
        contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=45)).date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Compute overdue status
        contract._compute_overdue_status()

        # Should be overdue (45 - 7 grace period = 38 days)
        self.assertGreater(
            contract.total_overdue_days,
            30,
            "Contract should be overdue more than 30 days"
        )

    def test_02_grace_period_no_penalties(self):
        """Test no penalties during grace period"""
        # Set grace period to 7 days
        self.env['ir.config_parameter'].sudo().set_param(
            'asset_finance.grace_period_days', 7
        )

        contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=5)).date(),
            penalty_rule_id=self.penalty_rule_daily.id
        )
        contract.action_approve()
        contract.action_generate_schedule()

        contract._compute_overdue_status()

        self.assertEqual(
            contract.total_overdue_days,
            0,
            "Should be 0 overdue days during grace period"
        )

    def test_03_late_status_attention(self):
        """Test late status changes to Attention after 30 days"""
        contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=40)).date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        contract._compute_overdue_status()

        self.assertEqual(
            contract.late_status,
            'attention',
            "Late status should be Attention after 30+ days"
        )

    def test_04_late_status_legal(self):
        """Test late status changes to Legal after 90 days"""
        contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=100)).date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        contract._compute_overdue_status()

        self.assertEqual(
            contract.late_status,
            'legal',
            "Late status should be Legal Action after 90+ days"
        )

    def test_05_penalty_calculation_daily_percent(self):
        """Test daily percentage penalty calculation"""
        contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=30)).date(),
            penalty_rule_id=self.penalty_rule_daily.id
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Run penalty cron
        self.env['finance.contract']._cron_calculate_late_interest()

        # Should have accrued penalties
        self.assertGreater(
            contract.accrued_penalty,
            0,
            "Should have accrued penalties"
        )

    def test_06_penalty_calculation_fixed_one_time(self):
        """Test fixed one-time penalty"""
        contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=15)).date(),
            penalty_rule_id=self.penalty_rule_fixed.id
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Run penalty cron
        self.env['finance.contract']._cron_calculate_late_interest()

        # Should have fixed penalty
        self.assertMoneyEqual(
            contract.accrued_penalty,
            50.0,  # Fixed amount from rule
            "Should have $50 fixed penalty"
        )

        # Run cron again - should not double charge
        self.env['finance.contract']._cron_calculate_late_interest()

        # Still $50 (not $100)
        self.assertMoneyEqual(
            contract.accrued_penalty,
            50.0,
            "Should not apply fixed penalty twice"
        )

    def test_07_send_reminder_action(self):
        """Test send payment reminder action"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Send reminder
        result = contract.action_send_reminder()

        # Check reminder date set
        self.assertIsNotNone(
            contract.date_reminder_sent,
            "Reminder date should be set"
        )

        # Check result is notification
        self.assertEqual(result['type'], 'ir.actions.client')

    def test_08_send_4th_schedule_changes_status(self):
        """Test sending 4th schedule changes status to Legal"""
        contract = self._create_test_contract()
        contract.action_approve()
        contract.late_status = 'attention'

        # Send 4th schedule
        result = contract.action_send_4th_schedule()

        # Status should be legal
        self.assertEqual(
            contract.late_status,
            'legal',
            "Status should change to Legal after 4th schedule"
        )

        # Date should be set
        self.assertIsNotNone(contract.date_4th_sched_sent)

    def test_09_issue_repo_order(self):
        """Test issuing repossession order"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Issue repo order
        result = contract.action_issue_repo_order()

        # Status should be repo
        self.assertEqual(
            contract.ac_status,
            'repo',
            "Contract status should be Repossessed"
        )

        # Asset status should be repo
        self.assertEqual(
            contract.asset_id.status,
            'repo',
            "Asset status should be Repossessed"
        )

        # Date should be set
        self.assertIsNotNone(contract.date_repo_order)

    def test_10_send_5th_schedule(self):
        """Test sending 5th schedule post-repo"""
        contract = self._create_test_contract()
        contract.action_approve()
        contract.action_issue_repo_order()

        # Send 5th schedule
        result = contract.action_send_5th_schedule()

        # Date should be set
        self.assertIsNotNone(contract.date_5th_sched_sent)

    def test_11_batch_send_reminders_success(self):
        """Test batch sending reminders"""
        # Create multiple contracts
        contracts = self.env['finance.contract']
        for i in range(3):
            contract = self._create_test_contract(
                asset_id=self.asset_1.id if i == 0 else self.asset_2.id,
                hirer_id=self.customer_1.id
            )
            contract.action_approve()
            contracts |= contract

        # Batch send
        result = contracts.action_batch_send_reminders()

        # Check success count
        self.assertEqual(result['type'], 'ir.actions.client')

    def test_12_batch_send_reminders_with_missing_email(self):
        """Test batch reminders with missing emails"""
        # Create contract with customer without email
        customer_no_email = self.env['res.partner'].create({
            'name': 'No Email Customer',
            'is_finance_customer': True,
        })

        contract = self._create_test_contract(hirer_id=customer_no_email.id)
        contract.action_approve()

        # Should handle gracefully
        result = contract.action_batch_send_reminders()

        # Should return result
        self.assertIsNotNone(result)

    def test_13_penalty_balance_calculation(self):
        """Test penalty balance calculation"""
        contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=30)).date(),
            penalty_rule_id=self.penalty_rule_daily.id
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Accrue some penalties
        contract.accrued_penalty = 500.0
        contract.total_late_paid = 200.0

        # Balance should be 300
        self.assertMoneyEqual(
            contract.balance_late_charges,
            300.0,
            "Balance late charges should be accrued - paid"
        )

    def test_14_cron_only_processes_active_contracts(self):
        """Test cron only processes active contracts"""
        # Create draft contract
        draft_contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=30)).date(),
            penalty_rule_id=self.penalty_rule_daily.id
        )

        # Create active contract
        active_contract = self._create_test_contract(
            asset_id=self.asset_2.id,
            first_due_date=(datetime.now() - timedelta(days=30)).date(),
            penalty_rule_id=self.penalty_rule_daily.id
        )
        active_contract.action_approve()
        active_contract.action_generate_schedule()

        # Run cron
        self.env['finance.contract']._cron_calculate_late_interest()

        # Draft should have no penalties
        self.assertEqual(
            draft_contract.accrued_penalty,
            0.0,
            "Draft contract should not accrue penalties"
        )

        # Active should have penalties
        self.assertGreater(
            active_contract.accrued_penalty,
            0.0,
            "Active contract should accrue penalties"
        )

    def test_15_settlement_quotation_action(self):
        """Test sending settlement quotation"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Send settlement quotation
        result = contract.action_send_settlement_quotation()

        # Should return notification
        self.assertEqual(result['type'], 'ir.actions.client')

    def test_16_overdue_with_no_unpaid_lines(self):
        """Test overdue calculation when all lines are paid"""
        contract = self._create_test_contract(
            first_due_date=datetime(2025, 1, 15).date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Mark all lines as paid
        for line in contract.line_ids:
            line.invoice_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': contract.hirer_id.id,
                'invoice_date': line.date_due,
                'payment_state': 'paid',
            })

        contract._compute_overdue_status()

        # Should have 0 overdue days
        self.assertEqual(
            contract.total_overdue_days,
            0,
            "Fully paid contract should have 0 overdue days"
        )

        # Status should be normal
        self.assertEqual(
            contract.late_status,
            'normal',
            "Late status should be normal for fully paid"
        )
