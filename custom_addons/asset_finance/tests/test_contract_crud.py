# -*- coding: utf-8 -*-
"""
Contract CRUD and Lifecycle Tests
==================================

Tests for contract creation, updates, deletion, and lifecycle workflow.
"""

from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged
from odoo.exceptions import ValidationError, UserError


@tagged('post_install', '-at_install', 'asset_finance', 'contract')
class TestContractCRUD(AssetFinanceTestCommon):
    """Test contract CRUD operations"""

    def test_01_create_contract_basic(self):
        """Test basic contract creation"""
        contract = self._create_test_contract()

        self.assertTrue(contract.id, "Contract should be created")
        self.assertEqual(contract.ac_status, 'draft', "New contract should be in draft status")
        self.assertTrue(contract.agreement_no, "Agreement number should be generated")
        self.assertNotEqual(contract.agreement_no, 'New', "Agreement number should not be 'New'")

    def test_02_create_contract_with_sequence(self):
        """Test agreement number sequence generation"""
        contract1 = self._create_test_contract()
        contract2 = self._create_test_contract(asset_id=self.asset_2.id)

        self.assertNotEqual(
            contract1.agreement_no,
            contract2.agreement_no,
            "Agreement numbers should be unique"
        )

    def test_03_contract_loan_amount_computation(self):
        """Test loan amount computation"""
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0
        )

        self.assertMoneyEqual(
            contract.loan_amount,
            40000.0,
            "Loan amount should be cash price - down payment"
        )

    def test_04_contract_term_charges_computation(self):
        """Test term charges (interest) computation"""
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id
        )

        # Expected: 40000 * 10% * 12/12 = 4000
        self.assertMoneyEqual(
            contract.term_charges,
            4000.0,
            "Term charges should be correctly calculated"
        )

    def test_05_contract_balance_hire_computation(self):
        """Test balance hire computation"""
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0,
            int_rate_pa=10.0,
            no_of_inst=self.term_12m.id
        )

        # Expected: 40000 + 4000 = 44000
        self.assertMoneyEqual(
            contract.balance_hire,
            44000.0,
            "Balance hire should be loan amount + term charges"
        )

    def test_06_hp_act_flag_below_limit(self):
        """Test HP Act flag when loan amount is below limit"""
        # Configure HP Act limit
        self.env['ir.config_parameter'].sudo().set_param('asset_finance.hp_act_limit', 55000.0)

        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0  # Loan: 40000
        )

        self.assertTrue(contract.is_hp_act, "HP Act should apply for loan <= $55,000")

    def test_07_hp_act_flag_above_limit(self):
        """Test HP Act flag when loan amount is above limit"""
        # Configure HP Act limit
        self.env['ir.config_parameter'].sudo().set_param('asset_finance.hp_act_limit', 55000.0)

        contract = self._create_test_contract(
            cash_price=70000.0,
            down_payment=10000.0  # Loan: 60000
        )

        self.assertFalse(contract.is_hp_act, "HP Act should not apply for loan > $55,000")

    def test_08_validation_down_payment_exceeds_cash_price(self):
        """Test validation: down payment cannot exceed cash price"""
        with self.assertRaises(ValidationError, msg="Should raise ValidationError"):
            self._create_test_contract(
                cash_price=50000.0,
                down_payment=60000.0  # Invalid!
            )

    def test_09_validation_negative_interest_rate(self):
        """Test validation: interest rate cannot be negative"""
        with self.assertRaises(ValidationError, msg="Should raise ValidationError"):
            self._create_test_contract(
                int_rate_pa=-5.0  # Invalid!
            )

    def test_10_validation_interest_rate_over_100(self):
        """Test validation: interest rate cannot exceed 100%"""
        with self.assertRaises(ValidationError, msg="Should raise ValidationError"):
            self._create_test_contract(
                int_rate_pa=150.0  # Invalid!
            )

    def test_11_validation_residual_value_percentage(self):
        """Test validation: residual value must be 0-100%"""
        with self.assertRaises(ValidationError, msg="Should raise ValidationError"):
            self._create_test_contract(
                residual_value_percent=150.0  # Invalid!
            )

    def test_12_contract_approve_workflow(self):
        """Test contract approval workflow"""
        contract = self._create_test_contract()

        # Initially draft
        self.assertEqual(contract.ac_status, 'draft')

        # Approve
        contract.action_approve()

        # Should be active
        self.assertEqual(contract.ac_status, 'active', "Contract should be active after approval")

    def test_13_contract_close_workflow(self):
        """Test contract close workflow"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Close contract
        contract.action_close()

        self.assertEqual(contract.ac_status, 'closed', "Contract should be closed")

    def test_14_contract_back_to_draft(self):
        """Test setting contract back to draft"""
        contract = self._create_test_contract()
        contract.action_approve()
        self.assertEqual(contract.ac_status, 'active')

        # Back to draft
        contract.action_draft()

        self.assertEqual(contract.ac_status, 'draft', "Contract should be back to draft")

    def test_15_maturity_date_computation(self):
        """Test maturity date computation"""
        contract = self._create_test_contract(
            no_of_inst=self.term_12m.id
        )
        contract.first_due_date = datetime(2025, 1, 15).date()

        # Force recompute
        contract._compute_maturity_date()

        # Expected: 2025-01-15 + 11 months = 2025-12-15
        expected_maturity = datetime(2025, 12, 15).date()
        self.assertEqual(
            contract.maturity_date,
            expected_maturity,
            f"Maturity date should be {expected_maturity}"
        )

    def test_16_onchange_product_sets_defaults(self):
        """Test product onchange sets default values"""
        contract = self.env['finance.contract'].new({
            'product_id': self.product_hp_5y.id,
        })

        contract._onchange_product()

        self.assertEqual(
            contract.int_rate_pa,
            self.product_hp_5y.default_int_rate,
            "Interest rate should be set from product"
        )

    def test_17_onchange_admin_fee(self):
        """Test admin fee onchange"""
        contract = self.env['finance.contract'].new({
            'admin_fee_id': self.admin_fee.id,
        })

        contract._onchange_admin_fee()

        self.assertMoneyEqual(
            contract.admin_fee,
            self.admin_fee.amount,
            "Admin fee should be set from charge"
        )

    def test_18_contract_with_guarantor(self):
        """Test contract with guarantor line"""
        contract = self._create_test_contract()

        guarantor_line = self.env['finance.contract.guarantor'].create({
            'contract_id': contract.id,
            'partner_id': self.guarantor.id,
            'relationship': 'spouse',
            'income_verified': True,
        })

        self.assertEqual(len(contract.guarantor_line_ids), 1, "Contract should have 1 guarantor")
        self.assertEqual(
            guarantor_line.partner_id.id,
            self.guarantor.id,
            "Guarantor should be correctly linked"
        )

    def test_19_contract_with_joint_hirer(self):
        """Test contract with joint hirer (co-borrower)"""
        contract = self._create_test_contract()

        joint_hirer = self.env['finance.contract.joint.hirer'].create({
            'contract_id': contract.id,
            'partner_id': self.customer_2.id,
            'relationship': 'spouse',
            'share_percentage': 50.0,
        })

        self.assertEqual(len(contract.joint_hirer_line_ids), 1, "Contract should have 1 co-borrower")
        self.assertMoneyEqual(joint_hirer.share_percentage, 50.0)

    def test_20_contract_delete_draft(self):
        """Test deleting a draft contract"""
        contract = self._create_test_contract()

        # Should be able to delete draft
        contract_id = contract.id
        contract.unlink()

        # Verify deleted
        deleted = self.env['finance.contract'].search([('id', '=', contract_id)])
        self.assertFalse(deleted, "Draft contract should be deleted")


@tagged('post_install', '-at_install', 'asset_finance', 'contract')
class TestContractLifecycle(AssetFinanceTestCommon):
    """Test contract lifecycle and state transitions"""

    def test_01_full_lifecycle_draft_to_closed(self):
        """Test full contract lifecycle from draft to closed"""
        # Create contract
        contract = self._create_test_contract()
        self.assertEqual(contract.ac_status, 'draft')

        # Approve
        contract.action_approve()
        self.assertEqual(contract.ac_status, 'active')

        # Close
        contract.action_close()
        self.assertEqual(contract.ac_status, 'closed')

    def test_02_draft_to_active_to_repo(self):
        """Test repossession workflow"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Issue repo order
        contract.action_issue_repo_order()

        self.assertEqual(contract.ac_status, 'repo', "Contract status should be repossessed")
        self.assertIsNotNone(contract.date_repo_order, "Repo date should be set")

    def test_03_payment_count_computation(self):
        """Test payment count computation"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Create a test payment
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': contract.hirer_id.id,
            'amount': 1000.0,
            'date': datetime.now().date(),
            'journal_id': self.bank_journal.id,
            'contract_id': contract.id,
        })

        contract._compute_payment_count()

        self.assertEqual(contract.payment_count, 1, "Payment count should be 1")

    def test_04_invoice_count_computation(self):
        """Test invoice count computation"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Create a test invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': contract.hirer_id.id,
            'invoice_date': datetime.now().date(),
            'invoice_origin': contract.agreement_no,
        })

        contract._compute_invoice_count()

        self.assertEqual(contract.invoice_count, 1, "Invoice count should be 1")

    def test_05_view_payments_action(self):
        """Test view payments action"""
        contract = self._create_test_contract()

        action = contract.action_view_payments()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.payment')
        self.assertIn(('contract_id', '=', contract.id), action['domain'])

    def test_06_view_invoices_action(self):
        """Test view invoices action"""
        contract = self._create_test_contract()

        action = contract.action_view_invoices()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.move')
        self.assertIn(('invoice_origin', '=', contract.agreement_no), action['domain'])


from datetime import datetime
