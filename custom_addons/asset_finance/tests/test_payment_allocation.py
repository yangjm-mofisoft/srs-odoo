# -*- coding: utf-8 -*-
"""
Payment Allocation Tests
=========================

Tests for payment allocation waterfall logic.
"""

from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged
from datetime import datetime


@tagged('post_install', '-at_install', 'asset_finance', 'payment')
class TestPaymentAllocation(AssetFinanceTestCommon):
    """Test payment allocation logic"""

    def _create_payment(self, contract, amount):
        """Helper to create a payment"""
        return self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': contract.hirer_id.id,
            'amount': amount,
            'date': datetime.now().date(),
            'journal_id': self.bank_journal.id,
            'contract_id': contract.id,
        })

    def test_01_payment_waterfall_penalties_first(self):
        """Test payment allocates to penalties first"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Set penalties
        contract.balance_late_charges = 300.0

        # Create payment
        payment = self._create_payment(contract, 500.0)
        payment.action_post()

        # Check allocation
        self.assertMoneyEqual(
            payment.allocated_to_penalties,
            300.0,
            "Should allocate $300 to penalties first"
        )

        # Remaining should go to installments
        remaining_to_installments = payment.allocated_to_principal + payment.allocated_to_interest
        self.assertMoneyEqual(
            remaining_to_installments,
            200.0,
            "Remaining $200 should go to installments"
        )

    def test_02_payment_full_penalty_clearance(self):
        """Test payment fully clears penalties"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Set penalties
        contract.balance_late_charges = 300.0
        initial_penalties = contract.balance_late_charges

        # Create payment
        payment = self._create_payment(contract, 1000.0)
        payment.action_post()

        # Penalties should be cleared
        self.assertMoneyEqual(
            contract.balance_late_charges,
            0.0,
            "Penalties should be fully cleared"
        )

        # Total late paid should equal initial penalties
        self.assertMoneyEqual(
            contract.total_late_paid,
            initial_penalties,
            "Total late paid should equal cleared penalties"
        )

    def test_03_payment_allocation_to_oldest_installment(self):
        """Test payment allocates to oldest installment first"""
        contract = self._create_test_contract(
            first_due_date=datetime(2024, 1, 15).date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Create invoices for first 3 installments
        for line in contract.line_ids.sorted('sequence')[:3]:
            line.invoice_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': contract.hirer_id.id,
                'invoice_date': line.date_due,
                'date': line.date_due,
                'journal_id': contract.journal_id.id,
                'invoice_origin': contract.agreement_no,
                'invoice_line_ids': [(0, 0, {
                    'name': f'Installment {line.sequence}',
                    'quantity': 1,
                    'price_unit': line.amount_total,
                    'account_id': contract.asset_account_id.id,
                })],
            })
            line.invoice_id.action_post()

        # Pay first installment only
        first_line = contract.line_ids.sorted('sequence')[0]
        payment = self._create_payment(contract, first_line.amount_total)
        payment.action_post()

        # Check allocations exist
        self.assertGreater(
            len(payment.payment_allocation_ids),
            0,
            "Should have payment allocation records"
        )

    def test_04_payment_partial_installment(self):
        """Test partial payment to installment"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Create invoice for first installment
        first_line = contract.line_ids.sorted('sequence')[0]
        first_line.invoice_id = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': contract.hirer_id.id,
            'invoice_date': first_line.date_due,
            'date': first_line.date_due,
            'journal_id': contract.journal_id.id,
            'invoice_origin': contract.agreement_no,
            'invoice_line_ids': [(0, 0, {
                'name': f'Installment {first_line.sequence}',
                'quantity': 1,
                'price_unit': first_line.amount_total,
                'account_id': contract.asset_account_id.id,
            })],
        })
        first_line.invoice_id.action_post()

        # Partial payment (half of installment)
        payment_amount = first_line.amount_total / 2
        payment = self._create_payment(contract, payment_amount)
        payment.action_post()

        # Should have partial allocation
        total_allocated = payment.allocated_to_principal + payment.allocated_to_interest
        self.assertMoneyEqual(
            total_allocated,
            payment_amount,
            "Should allocate partial amount"
        )

    def test_05_payment_overpayment(self):
        """Test overpayment handling"""
        contract = self._create_test_contract(
            cash_price=10000.0,
            down_payment=0.0,
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Create invoice for first installment only
        first_line = contract.line_ids.sorted('sequence')[0]
        first_line.invoice_id = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': contract.hirer_id.id,
            'invoice_date': first_line.date_due,
            'date': first_line.date_due,
            'journal_id': contract.journal_id.id,
            'invoice_origin': contract.agreement_no,
            'invoice_line_ids': [(0, 0, {
                'name': f'Installment {first_line.sequence}',
                'quantity': 1,
                'price_unit': first_line.amount_total,
                'account_id': contract.asset_account_id.id,
            })],
        })
        first_line.invoice_id.action_post()

        # Overpay (pay more than due)
        overpayment_amount = first_line.amount_total * 2
        payment = self._create_payment(contract, overpayment_amount)
        payment.action_post()

        # Should allocate to available installments
        total_allocated = payment.allocated_to_principal + payment.allocated_to_interest
        self.assertGreater(
            total_allocated,
            0,
            "Should allocate available amount"
        )

    def test_06_payment_allocation_principal_interest_split(self):
        """Test payment splits between principal and interest"""
        contract = self._create_test_contract(
            cash_price=10000.0,
            down_payment=0.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id,
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Create invoice for first installment
        first_line = contract.line_ids.sorted('sequence')[0]
        first_line.invoice_id = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': contract.hirer_id.id,
            'invoice_date': first_line.date_due,
            'date': first_line.date_due,
            'journal_id': contract.journal_id.id,
            'invoice_origin': contract.agreement_no,
            'invoice_line_ids': [(0, 0, {
                'name': f'Installment {first_line.sequence}',
                'quantity': 1,
                'price_unit': first_line.amount_total,
                'account_id': contract.asset_account_id.id,
            })],
        })
        first_line.invoice_id.action_post()

        # Pay full installment
        payment = self._create_payment(contract, first_line.amount_total)
        payment.action_post()

        # Should have both principal and interest allocated
        self.assertGreater(
            payment.allocated_to_principal,
            0,
            "Should allocate some to principal"
        )

        self.assertGreater(
            payment.allocated_to_interest,
            0,
            "Should allocate some to interest"
        )

        # Sum should equal payment amount
        total_allocated = (
            payment.allocated_to_penalties +
            payment.allocated_to_principal +
            payment.allocated_to_interest
        )
        self.assertMoneyEqual(
            total_allocated,
            payment.amount,
            "Total allocated should equal payment amount"
        )

    def test_07_multiple_payments_cumulative(self):
        """Test multiple payments accumulate correctly"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Set penalties
        contract.balance_late_charges = 500.0

        # First payment - partial penalty
        payment1 = self._create_payment(contract, 200.0)
        payment1.action_post()

        self.assertMoneyEqual(
            contract.total_late_paid,
            200.0,
            "First payment should pay $200 towards penalties"
        )

        # Second payment - rest of penalty
        payment2 = self._create_payment(contract, 300.0)
        payment2.action_post()

        self.assertMoneyEqual(
            contract.total_late_paid,
            500.0,
            "Total late paid should be $500 after both payments"
        )

        self.assertMoneyEqual(
            contract.balance_late_charges,
            0.0,
            "Penalties should be fully cleared"
        )

    def test_08_payment_allocation_logged_to_chatter(self):
        """Test payment allocation is logged to chatter"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Create payment
        payment = self._create_payment(contract, 1000.0)
        payment.action_post()

        # Check chatter has message
        messages = contract.message_ids
        allocation_messages = messages.filtered(
            lambda m: 'Payment' in (m.body or '') and 'allocated' in (m.body or '')
        )

        self.assertTrue(
            len(allocation_messages) > 0,
            "Should log allocation to chatter"
        )

    def test_09_payment_without_contract(self):
        """Test payment without contract link doesn't allocate"""
        # Create payment without contract_id
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer_1.id,
            'amount': 1000.0,
            'date': datetime.now().date(),
            'journal_id': self.bank_journal.id,
            # No contract_id
        })

        payment.action_post()

        # Should have no allocations
        self.assertEqual(
            len(payment.payment_allocation_ids),
            0,
            "Payment without contract should not create allocations"
        )

    def test_10_payment_outbound_no_allocation(self):
        """Test outbound payments don't trigger allocation"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Create outbound payment
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',  # Not inbound
            'partner_type': 'supplier',
            'partner_id': self.supplier.id,
            'amount': 1000.0,
            'date': datetime.now().date(),
            'journal_id': self.bank_journal.id,
            'contract_id': contract.id,
        })

        payment.action_post()

        # Should have no allocations
        self.assertEqual(
            len(payment.payment_allocation_ids),
            0,
            "Outbound payment should not create allocations"
        )
