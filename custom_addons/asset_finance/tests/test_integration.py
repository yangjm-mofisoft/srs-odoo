# -*- coding: utf-8 -*-
"""
Integration Tests
=================

Tests for integration between modules and full workflows.
"""

from .test_common import AssetFinanceTestCommon
from odoo.tests.common import tagged
from datetime import datetime, timedelta


@tagged('post_install', '-at_install', 'asset_finance', 'integration')
class TestIntegration(AssetFinanceTestCommon):
    """Test integration workflows"""

    def test_01_full_contract_lifecycle(self):
        """Test complete contract lifecycle from creation to closure"""
        # Step 1: Create contract
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0,
            int_rate_pa=8.5,
            no_of_inst=self.term_12m.id,
            first_due_date=datetime.now().date()
        )

        self.assertEqual(contract.ac_status, 'draft')

        # Step 2: Generate schedule
        contract.action_generate_schedule()
        self.assertEqual(len(contract.line_ids), 12)

        # Step 3: Approve
        contract.action_approve()
        self.assertEqual(contract.ac_status, 'active')

        # Step 4: Disburse
        move = contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )
        self.assertTrue(move.id)

        # Step 5: Create invoices
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

        # Step 6: Register payment
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': contract.hirer_id.id,
            'amount': first_line.amount_total,
            'date': datetime.now().date(),
            'journal_id': self.bank_journal.id,
            'contract_id': contract.id,
        })
        payment.action_post()

        # Step 7: Close contract
        contract.action_close()
        self.assertEqual(contract.ac_status, 'closed')

    def test_02_collection_escalation_workflow(self):
        """Test full collection escalation workflow"""
        contract = self._create_test_contract(
            first_due_date=(datetime.now() - timedelta(days=100)).date(),
            penalty_rule_id=self.penalty_rule_daily.id
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Compute overdue
        contract._compute_overdue_status()

        # Should be in legal status (90+ days)
        self.assertEqual(contract.late_status, 'legal')

        # Send reminder
        contract.action_send_reminder()
        self.assertIsNotNone(contract.date_reminder_sent)

        # Send 4th schedule
        contract.action_send_4th_schedule()
        self.assertIsNotNone(contract.date_4th_sched_sent)

        # Issue repo order
        contract.action_issue_repo_order()
        self.assertEqual(contract.ac_status, 'repo')

        # Send 5th schedule
        contract.action_send_5th_schedule()
        self.assertIsNotNone(contract.date_5th_sched_sent)

    def test_03_early_settlement_workflow(self):
        """Test early settlement workflow"""
        contract = self._create_test_contract(
            cash_price=50000.0,
            down_payment=10000.0,
            int_rate_pa=8.0,
            no_of_inst=self.term_60m.id,
            first_due_date=datetime(2025, 1, 15).date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Pay first 24 installments
        for line in contract.line_ids.sorted('sequence')[:24]:
            line.invoice_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': contract.hirer_id.id,
                'invoice_date': line.date_due,
                'payment_state': 'paid',
            })

        # Calculate settlement
        settlement_date = datetime(2027, 1, 15).date()
        settlement_info = contract.calculate_settlement_amount(settlement_date)

        self.assertGreater(settlement_info['settlement_amount'], 0)

        # Process settlement
        move = contract.process_early_settlement(
            settlement_date=settlement_date,
            payment_journal_id=self.bank_journal.id
        )

        # Verify closed
        self.assertEqual(contract.ac_status, 'closed')
        self.assertTrue(move.id)

    def test_04_payment_allocation_workflow(self):
        """Test payment allocation across penalties and installments"""
        contract = self._create_test_contract(
            first_due_date=datetime.now().date()
        )
        contract.action_approve()
        contract.action_generate_schedule()

        # Set up test scenario
        contract.balance_late_charges = 500.0

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

        # Make payment covering penalties and 2 installments
        first_line = contract.line_ids.sorted('sequence')[0]
        payment_amount = 500.0 + (first_line.amount_total * 2)

        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': contract.hirer_id.id,
            'amount': payment_amount,
            'date': datetime.now().date(),
            'journal_id': self.bank_journal.id,
            'contract_id': contract.id,
        })
        payment.action_post()

        # Verify allocation
        self.assertMoneyEqual(payment.allocated_to_penalties, 500.0)
        self.assertGreater(payment.allocated_to_principal, 0)
        self.assertGreater(payment.allocated_to_interest, 0)

    def test_05_multi_user_concurrent_access(self):
        """Test multiple users accessing same contract"""
        contract = self._create_test_contract()

        # Officer creates contract
        self.assertEqual(contract.ac_status, 'draft')

        # Officer can read
        contract_as_officer = contract.with_user(self.user_officer)
        self.assertEqual(contract_as_officer.id, contract.id)

        # Manager approves
        contract.with_user(self.user_manager).action_approve()
        self.assertEqual(contract.ac_status, 'active')

        # Collection can now see it
        contract_as_collection = self.env['finance.contract'].with_user(
            self.user_collection
        ).search([('id', '=', contract.id)])
        self.assertTrue(contract_as_collection)

    def test_06_dashboard_kpi_accuracy(self):
        """Test dashboard KPIs reflect contract data"""
        # Create multiple contracts
        contracts = []
        for i in range(3):
            contract = self._create_test_contract(
                asset_id=self.asset_1.id if i == 0 else self.asset_2.id,
                hirer_id=self.customer_1.id if i < 2 else self.customer_2.id
            )
            contract.action_approve()
            contracts.append(contract)

        # Get dashboard
        dashboard = self.env['finance.dashboard'].search([], limit=1)
        dashboard._compute_kpis()

        # Verify active contracts count
        self.assertEqual(
            dashboard.total_active_contracts,
            3,
            "Dashboard should show 3 active contracts"
        )

        # Verify portfolio value
        expected_portfolio = sum(c.os_balance for c in contracts)
        self.assertMoneyEqual(
            dashboard.total_portfolio_value,
            expected_portfolio,
            "Portfolio value should match sum of contracts"
        )

    def test_07_fleet_integration(self):
        """Test integration with fleet module"""
        # Vehicle should exist
        self.assertTrue(self.vehicle_1.id)

        # Asset should link to vehicle
        self.assertEqual(self.asset_1.vehicle_id.id, self.vehicle_1.id)

        # Contract should access vehicle details
        contract = self._create_test_contract()
        self.assertEqual(contract.asset_reg_no, 'TEST1234A')
        self.assertTrue(contract.asset_make)  # Should get from vehicle

    def test_08_partner_integration(self):
        """Test integration with partner/customer module"""
        # Customer should exist
        self.assertTrue(self.customer_1.id)

        # Contract should link to customer
        contract = self._create_test_contract()
        self.assertEqual(contract.hirer_id.id, self.customer_1.id)

        # Should access customer details
        self.assertEqual(contract.hirer_id.email, 'customer1@test.com')

    def test_09_accounting_integration(self):
        """Test integration with accounting module"""
        contract = self._create_test_contract()
        contract.action_approve()

        # Should create journal entries
        move = contract.create_disbursement_entry(
            disbursement_date=datetime.now().date(),
            payment_method_id=self.bank_journal.id
        )

        # Entry should be in accounting
        move_found = self.env['account.move'].search([('id', '=', move.id)])
        self.assertTrue(move_found)

        # Should use configured accounts
        self.assertIn(contract.asset_account_id, move.line_ids.mapped('account_id'))

    def test_10_report_generation(self):
        """Test report views generate data"""
        # Create test contracts
        contract1 = self._create_test_contract()
        contract1.action_approve()

        contract2 = self._create_test_contract(
            asset_id=self.asset_2.id,
            hirer_id=self.customer_2.id
        )
        contract2.action_approve()

        # Test aging report
        aging_records = self.env['finance.report.aging'].search([])
        self.assertTrue(len(aging_records) > 0, "Aging report should have data")

    def test_11_configuration_persistence(self):
        """Test configuration parameters persist across sessions"""
        # Set configuration
        self.env['ir.config_parameter'].sudo().set_param(
            'asset_finance.hp_act_limit', 60000.0
        )

        # Retrieve configuration
        param = self.env['ir.config_parameter'].sudo().search([('key', '=', 'asset_finance.hp_act_limit')], limit=1)
        hp_limit = float(param.value) if param else 55000.0

        self.assertEqual(hp_limit, 60000.0, "Configuration should persist")

    def test_12_product_constraints_integration(self):
        """Test product constraints apply to contracts"""
        # Product with date constraints
        product_limited = self.env['finance.product'].create({
            'name': 'Limited Product',
            'product_type': 'hp',
            'default_int_rate': 8.0,
            'date_start': datetime(2025, 1, 1).date(),
            'date_end': datetime(2025, 12, 31).date(),
            'min_months': 12,
            'max_months': 60,
            'step_months': 12,
        })

        # Contract within validity
        contract_valid = self._create_test_contract(
            product_id=product_limited.id,
            agreement_date=datetime(2025, 6, 15).date()
        )
        self.assertTrue(contract_valid.id)

    def test_13_guarantor_coborrower_workflow(self):
        """Test contracts with guarantors and co-borrowers"""
        contract = self._create_test_contract()

        # Add guarantor
        guarantor = self.env['finance.contract.guarantor'].create({
            'contract_id': contract.id,
            'partner_id': self.guarantor.id,
            'relationship': 'spouse',
            'income_verified': True,
        })

        # Add co-borrower
        joint_hirer = self.env['finance.contract.joint.hirer'].create({
            'contract_id': contract.id,
            'partner_id': self.customer_2.id,
            'relationship': 'spouse',
            'share_percentage': 50.0,
        })

        # Verify
        self.assertEqual(len(contract.guarantor_line_ids), 1)
        self.assertEqual(len(contract.joint_hirer_line_ids), 1)

        # Approve contract with guarantor/co-borrower
        contract.action_approve()
        self.assertEqual(contract.ac_status, 'active')
