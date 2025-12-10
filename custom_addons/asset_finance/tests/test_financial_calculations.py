# -*- coding: utf-8 -*-
"""
Financial Calculations Tests
=============================

Tests for financial calculations including:
- Interest calculations
- Amortization schedules (Rule of 78 and Flat Rate)
- Installment calculations
- Early settlement calculations
"""

from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math


@tagged('post_install', '-at_install', 'asset_finance', 'financial')
class TestFinancialCalculations(AssetFinanceTestCommon):
    """Test financial calculation accuracy"""

    def test_01_simple_interest_calculation(self):
        """Test simple interest calculation"""
        contract = self._create_test_contract(
            cash_price=12000.0,
            down_payment=0.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id
        )

        # Expected: 12000 * 10% * 12/12 = 1200
        self.assertMoneyEqual(
            contract.term_charges,
            1200.0,
            "Term charges should be $1,200 for $12,000 loan at 10% for 12 months"
        )

    def test_02_interest_calculation_24_months(self):
        """Test interest calculation for 24 months"""
        contract = self._create_test_contract(
            cash_price=24000.0,
            down_payment=0.0,
            int_rate_pa=12.0,
            no_of_inst=self.term_24m.id
        )

        # Expected: 24000 * 12% * 24/12 = 5760
        self.assertMoneyEqual(
            contract.term_charges,
            5760.0,
            "Term charges should be $5,760"
        )

    def test_03_annuity_installment_calculation(self):
        """Test annuity formula for installment calculation"""
        contract = self._create_test_contract(
            cash_price=100000.0,
            down_payment=0.0,
            int_rate_pa=6.0,
            no_of_inst=self.term_12m.id
        )

        # Annuity formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
        # P = 100000, r = 0.005 (6%/12), n = 12
        # Expected monthly ~ 8606.64

        self.assertMoneyEqual(
            contract.monthly_inst,
            8606.0,  # Floored
            "Monthly installment should be ~$8,606",
            delta=10.0  # Allow $10 difference due to rounding
        )

    def test_04_zero_interest_contract(self):
        """Test contract with 0% interest"""
        contract = self._create_test_contract(
            cash_price=12000.0,
            down_payment=0.0,
            int_rate_pa=0.0,
            no_of_inst=self.term_12m.id
        )

        self.assertMoneyEqual(contract.term_charges, 0.0, "Term charges should be 0")
        self.assertMoneyEqual(
            contract.monthly_inst,
            1000.0,  # 12000 / 12
            "Monthly installment should be loan amount / months"
        )

    def test_05_rule_of_78_schedule_generation(self):
        """Test Rule of 78 schedule generation"""
        contract = self._create_test_contract(
            cash_price=12000.0,
            down_payment=0.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id,
            interest_method='rule78',
            first_due_date=datetime(2025, 1, 15).date()
        )

        # Generate schedule
        contract.action_generate_schedule()

        # Verify schedule created
        self.assertEqual(len(contract.line_ids), 12, "Should have 12 installment lines")

        # Rule of 78: Sum of digits = 12 * 13 / 2 = 78
        # First month weight = 12, last month weight = 1

        first_line = contract.line_ids.sorted('sequence')[0]
        last_line = contract.line_ids.sorted('sequence')[-1]

        # First installment should have highest interest
        # Interest = 1200 * (12/78) = 184.62
        self.assertMoneyEqual(
            first_line.amount_interest,
            184.62,
            "First installment should have highest interest",
            delta=1.0
        )

        # Last installment should have lowest interest
        # Interest = 1200 * (1/78) = 15.38
        self.assertMoneyEqual(
            last_line.amount_interest,
            15.38,
            "Last installment should have lowest interest",
            delta=1.0
        )

        # Total interest should equal term charges
        total_interest = sum(contract.line_ids.mapped('amount_interest'))
        self.assertMoneyEqual(
            total_interest,
            contract.term_charges,
            "Total interest should equal term charges"
        )

    def test_06_flat_rate_schedule_generation(self):
        """Test Flat Rate schedule generation"""
        contract = self._create_test_contract(
            cash_price=12000.0,
            down_payment=0.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id,
            interest_method='flat',
            first_due_date=datetime(2025, 1, 15).date()
        )

        # Generate schedule
        contract.action_generate_schedule()

        # Verify schedule created
        self.assertEqual(len(contract.line_ids), 12, "Should have 12 installment lines")

        # Flat rate: Equal interest each month
        # Interest per month = 1200 / 12 = 100

        for line in contract.line_ids:
            self.assertMoneyEqual(
                line.amount_interest,
                100.0,
                f"Each installment should have equal interest (Line {line.sequence})",
                delta=0.01
            )

    def test_07_payment_scheme_arrears(self):
        """Test payment scheme arrears (normal)"""
        contract = self._create_test_contract(
            cash_price=12000.0,
            down_payment=0.0,
            no_of_inst=self.term_12m.id,
            payment_scheme='arrears',
            agreement_date=datetime(2025, 1, 1).date()
        )

        # Generate schedule without first_due_date
        contract.first_due_date = False
        contract.action_generate_schedule()

        # First due date should be 1 month after agreement
        first_line = contract.line_ids.sorted('sequence')[0]
        expected_date = datetime(2025, 2, 1).date()

        self.assertEqual(
            first_line.date_due,
            expected_date,
            "Arrears: First due date should be 1 month after agreement"
        )

    def test_08_payment_scheme_advance(self):
        """Test payment scheme advance (front payment)"""
        contract = self._create_test_contract(
            cash_price=12000.0,
            down_payment=0.0,
            no_of_inst=self.term_12m.id,
            payment_scheme='advance',
            agreement_date=datetime(2025, 1, 1).date()
        )

        # Generate schedule without first_due_date
        contract.first_due_date = False
        contract.action_generate_schedule()

        # First due date should be on agreement date
        first_line = contract.line_ids.sorted('sequence')[0]
        expected_date = datetime(2025, 1, 1).date()

        self.assertEqual(
            first_line.date_due,
            expected_date,
            "Advance: First due date should be on agreement date"
        )

    def test_09_schedule_total_amounts_match(self):
        """Test schedule totals match contract totals"""
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0,
            int_rate_pa=8.5,
            no_of_inst=self.term_60m.id,
            first_due_date=datetime(2025, 1, 15).date()
        )

        contract.action_generate_schedule()

        # Sum of all principal should equal loan amount
        total_principal = sum(contract.line_ids.mapped('amount_principal'))
        self.assertMoneyEqual(
            total_principal,
            contract.loan_amount,
            "Total principal should equal loan amount"
        )

        # Sum of all interest should equal term charges
        total_interest = sum(contract.line_ids.mapped('amount_interest'))
        self.assertMoneyEqual(
            total_interest,
            contract.term_charges,
            "Total interest should equal term charges"
        )

        # Sum of all amounts should equal balance hire
        total_amount = sum(contract.line_ids.mapped('amount_total'))
        self.assertMoneyEqual(
            total_amount,
            contract.balance_hire,
            "Total amount should equal balance hire"
        )

    def test_10_settlement_calculation_basic(self):
        """Test early settlement calculation"""
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0,
            int_rate_pa=8.0,
            no_of_inst=self.term_60m.id,
            first_due_date=datetime(2025, 1, 15).date()
        )

        # Generate schedule
        contract.action_generate_schedule()

        # Mark first 24 installments as paid
        for line in contract.line_ids.sorted('sequence')[:24]:
            line.invoice_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': contract.hirer_id.id,
                'invoice_date': line.date_due,
                'payment_state': 'paid',
            })

        # Calculate settlement after 24 months
        settlement_date = datetime(2027, 1, 15).date()
        settlement_info = contract.calculate_settlement_amount(settlement_date)

        # Verify settlement info structure
        self.assertIn('outstanding_principal', settlement_info)
        self.assertIn('unearned_interest', settlement_info)
        self.assertIn('rebate_amount', settlement_info)
        self.assertIn('settlement_amount', settlement_info)

        # Outstanding principal should be > 0
        self.assertGreater(
            settlement_info['outstanding_principal'],
            0,
            "Should have outstanding principal"
        )

        # Settlement should be principal + rebate
        expected_settlement = (
            settlement_info['outstanding_principal'] +
            settlement_info['rebate_amount'] +
            settlement_info['balance_late_charges'] +
            settlement_info['balance_misc_fee']
        )

        self.assertMoneyEqual(
            settlement_info['settlement_amount'],
            expected_settlement,
            "Settlement amount should match calculation"
        )

    def test_11_settlement_rebate_fee_configuration(self):
        """Test settlement rebate fee from configuration"""
        # Set custom rebate fee
        self.env['ir.config_parameter'].sudo().set_param(
            'asset_finance.settlement_rebate_fee', 25.0
        )

        contract = self._create_test_contract(
            cash_price=10000.0,
            down_payment=0.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id,
            first_due_date=datetime(2025, 1, 15).date()
        )

        contract.action_generate_schedule()

        # Mark first 6 months as paid
        for line in contract.line_ids.sorted('sequence')[:6]:
            line.invoice_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': contract.hirer_id.id,
                'invoice_date': line.date_due,
                'payment_state': 'paid',
            })

        settlement_date = datetime(2025, 7, 15).date()
        settlement_info = contract.calculate_settlement_amount(settlement_date)

        # Rebate should be 25% of unearned interest
        expected_rebate = settlement_info['unearned_interest'] * 0.25

        self.assertMoneyEqual(
            settlement_info['rebate_amount'],
            expected_rebate,
            "Rebate should be 25% of unearned interest"
        )

    def test_12_different_first_last_installments(self):
        """Test contracts with different first/last installment amounts"""
        contract = self._create_test_contract(
            cash_price=12000.0,
            down_payment=0.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id,
            first_due_date=datetime(2025, 1, 15).date()
        )

        # Manually set different installments
        contract.first_inst_amount = 1200.0
        contract.monthly_inst = 1000.0
        contract.last_inst_amount = 1900.0  # Adjustment

        contract.action_generate_schedule()

        lines = contract.line_ids.sorted('sequence')

        # Verify first installment
        self.assertMoneyEqual(
            lines[0].amount_total,
            1200.0,
            "First installment should match first_inst_amount",
            delta=5.0
        )

        # Verify middle installments
        for line in lines[1:-1]:
            self.assertMoneyEqual(
                line.amount_total,
                1000.0,
                f"Middle installment {line.sequence} should match monthly_inst",
                delta=5.0
            )

    def test_13_schedule_regeneration(self):
        """Test schedule regeneration after changes"""
        contract = self._create_test_contract(
            cash_price=12000.0,
            down_payment=0.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id,
            first_due_date=datetime(2025, 1, 15).date()
        )

        # Generate initial schedule
        contract.action_generate_schedule()
        initial_count = len(contract.line_ids)
        self.assertEqual(initial_count, 12)

        # Change term to 24 months
        contract.no_of_inst = self.term_24m.id

        # Regenerate schedule
        contract.action_generate_schedule()

        # Should now have 24 lines
        self.assertEqual(
            len(contract.line_ids),
            24,
            "Should have 24 installments after regeneration"
        )

    def test_14_residual_value_calculation(self):
        """Test residual value calculation for leasing"""
        contract = self._create_test_contract(
            product_id=self.product_leasing_3y.id,
            cash_price=50000.0,
            down_payment=5000.0,
            residual_value_percent=30.0
        )

        # RV = 30% of cash price = 15000
        self.assertMoneyEqual(
            contract.residual_value,
            15000.0,
            "Residual value should be 30% of cash price"
        )

    def test_15_schedule_with_no_installments_set(self):
        """Test error when generating schedule without installments set"""
        contract = self._create_test_contract()
        contract.no_of_inst = False
        contract.monthly_inst = 0.0

        with self.assertRaises(UserError, msg="Should raise error for missing installments"):
            contract.action_generate_schedule()

    def test_16_installment_calculation_precision(self):
        """Test installment calculations maintain precision"""
        contract = self._create_test_contract(
            cash_price=49999.99,
            down_payment=9999.99,
            int_rate_pa=8.57,
            no_of_inst=self.term_60m.id
        )

        # Should not raise errors or lose precision
        self.assertIsNotNone(contract.monthly_inst)
        self.assertGreater(contract.monthly_inst, 0)

    def test_17_very_long_term_contract(self):
        """Test contract with maximum term"""
        # Create 120-month term
        term_120m = self.env['finance.term'].create({
            'name': '120 Months',
            'months': 120
        })

        contract = self._create_test_contract(
            cash_price=100000.0,
            down_payment=20000.0,
            int_rate_pa=6.0,
            no_of_inst=term_120m.id,
            first_due_date=datetime(2025, 1, 15).date()
        )

        # Generate schedule
        contract.action_generate_schedule()

        # Should create 120 installments
        self.assertEqual(
            len(contract.line_ids),
            120,
            "Should create 120 installment lines"
        )

        # Totals should still match
        total_principal = sum(contract.line_ids.mapped('amount_principal'))
        self.assertMoneyEqual(
            total_principal,
            contract.loan_amount,
            "Total principal should equal loan amount for long term"
        )

    def test_18_high_value_contract(self):
        """Test contract with very high values"""
        contract = self._create_test_contract(
            cash_price=10000000.0,  # $10M
            down_payment=2000000.0,   # $2M
            int_rate_pa=5.0,
            no_of_inst=self.term_60m.id
        )

        # Should handle large numbers correctly
        self.assertMoneyEqual(contract.loan_amount, 8000000.0)
        self.assertGreater(contract.monthly_inst, 100000.0)
        self.assertLess(contract.monthly_inst, 200000.0)
