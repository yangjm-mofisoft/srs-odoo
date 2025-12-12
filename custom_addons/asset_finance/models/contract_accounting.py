from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FinanceContract(models.Model):
    _inherit = 'finance.contract'

    # --------------------------------------------------------
    # DISBURSEMENT LOGIC
    # --------------------------------------------------------

    def action_disburse(self):
        """Open disbursement wizard"""
        self.ensure_one()
        if self.disbursement_move_id:
            raise UserError(_("Disbursement Entry already created!"))

        return {
            'name': 'Disbursement',
            'type': 'ir.actions.act_window',
            'res_model': 'finance.disbursement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id, 'active_id': self.id}
        }

    def create_disbursement_entry(self, disbursement_date, payment_method_id, bank_account_id=None):
        """
        Create the disbursement journal entry
        Called from disbursement wizard

        Accounting Entry:
        Dr. Finance Asset/Receivable Account    [Loan Amount]
        Dr. Supplier Account (Commission)       [Commission]
        Dr. Admin Fee Expense                   [Admin Fee]
            Cr. Bank/Cash Account               [Total Disbursed]
            Cr. Unearned Interest               [Term Charges]
        """
        self.ensure_one()

        if self.disbursement_move_id:
            raise UserError(_("Disbursement already processed!"))

        # Get journal for disbursements (should be Bank/Cash journal)
        journal = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash']),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not journal:
            raise UserError(_("No Bank or Cash journal found. Please configure accounting journals."))

        # Prepare line items
        line_items = []

        # 1. Debit: Finance Asset/Receivable (Loan Amount)
        line_items.append((0, 0, {
            'name': f'Disbursement - {self.agreement_no} (Principal)',
            'account_id': self.asset_account_id.id,
            'debit': self.loan_amount,
            'credit': 0,
            'partner_id': self.hirer_id.id,
        }))

        # 2. Credit: Unearned Interest (Liability)
        if self.term_charges > 0:
            line_items.append((0, 0, {
                'name': f'Unearned Interest - {self.agreement_no}',
                'account_id': self.unearned_interest_account_id.id,
                'debit': 0,
                'credit': self.term_charges,
            }))

        # 3. Debit: Commission to Supplier (if any)
        if self.commission > 0 and self.supplier_id:
            commission_account = self.supplier_id.property_account_payable_id
            line_items.append((0, 0, {
                'name': f'Commission - {self.agreement_no}',
                'account_id': commission_account.id,
                'debit': 0,
                'credit': self.commission,
                'partner_id': self.supplier_id.id,
            }))

        # 4. Debit: Admin Fee (if any)
        if self.admin_fee > 0:
            # Use a configured expense account for admin fees
            param = self.env['ir.config_parameter'].sudo().search([('key', '=', 'asset_finance.admin_fee_account_id')], limit=1)
            admin_fee_account = param.value if param else False
            if admin_fee_account:
                line_items.append((0, 0, {
                    'name': f'Admin Fee - {self.agreement_no}',
                    'account_id': int(admin_fee_account),
                    'debit': self.admin_fee,
                    'credit': 0,
                }))

        # 5. Credit: Bank/Cash (Total paid out)
        total_disbursed = self.loan_amount - self.commission - self.admin_fee
        if bank_account_id:
            bank_account = self.env['account.account'].browse(bank_account_id)
        else:
            bank_account = journal.default_account_id

        line_items.append((0, 0, {
            'name': f'Cash Disbursement - {self.agreement_no}',
            'account_id': bank_account.id,
            'debit': 0,
            'credit': total_disbursed,
            'partner_id': self.hirer_id.id,
        }))

        # Create Journal Entry
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': disbursement_date,
            'ref': f'Disbursement for {self.agreement_no}',
            'line_ids': line_items,
        })

        # Post the entry
        move.action_post()

        # Link to contract
        self.disbursement_move_id = move.id
        self.ac_status = 'active'

        # Log in chatter
        self.message_post(
            body=f"Disbursement Entry created: {move.name}<br/>"
                 f"Amount: {self.currency_id.symbol}{total_disbursed:,.2f}<br/>"
                 f"Date: {disbursement_date}"
        )

        return move

    def action_view_disbursement(self):
        """Open the disbursement journal entry"""
        self.ensure_one()
        if not self.disbursement_move_id:
            raise UserError(_("No disbursement entry found for this contract."))

        return {
            'name': 'Disbursement Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.disbursement_move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # --------------------------------------------------------
    # SETTLEMENT ACCOUNTING
    # --------------------------------------------------------

    def process_early_settlement(self, settlement_date, payment_journal_id, payment_ref=None):
        """
        Process early settlement accounting entries
        Called from settlement wizard

        Accounting Entry:
        Dr. Bank Account                        [Settlement Amount Received]
        Dr. Unearned Interest (Rebate Waived)   [Unearned Interest - Rebate]
            Cr. Finance Asset/Receivable        [Outstanding Principal]
            Cr. Income (Rebate Fee)              [Rebate Amount]
            Cr. Penalty Account                  [Balance Late Charges]
        """
        self.ensure_one()

        # Calculate settlement breakdown
        settlement_info = self.calculate_settlement_amount(settlement_date)

        # Get payment journal
        payment_journal = self.env['account.journal'].browse(payment_journal_id)

        # Prepare journal entry lines
        line_items = []

        # 1. Debit: Bank (Settlement amount received)
        line_items.append((0, 0, {
            'name': f'Settlement Payment - {self.agreement_no}',
            'account_id': payment_journal.default_account_id.id,
            'debit': settlement_info['settlement_amount'],
            'credit': 0,
            'partner_id': self.hirer_id.id,
        }))

        # 2. Debit: Unearned Interest (Write-off unearned portion minus rebate)
        unearned_writeoff = settlement_info['unearned_interest'] - settlement_info['rebate_amount']
        if unearned_writeoff > 0:
            line_items.append((0, 0, {
                'name': f'Unearned Interest Write-off - {self.agreement_no}',
                'account_id': self.unearned_interest_account_id.id,
                'debit': unearned_writeoff,
                'credit': 0,
            }))

        # 3. Credit: Finance Asset/Receivable (Outstanding Principal)
        line_items.append((0, 0, {
            'name': f'Settlement - Principal - {self.agreement_no}',
            'account_id': self.asset_account_id.id,
            'debit': 0,
            'credit': settlement_info['outstanding_principal'],
            'partner_id': self.hirer_id.id,
        }))

        # 4. Credit: Income Account (Rebate Fee - Early Settlement Income)
        if settlement_info['rebate_amount'] > 0:
            line_items.append((0, 0, {
                'name': f'Settlement Rebate Fee - {self.agreement_no}',
                'account_id': self.income_account_id.id,
                'debit': 0,
                'credit': settlement_info['rebate_amount'],
            }))

        # 5. Credit: Penalty Account (if penalties outstanding)
        if settlement_info['balance_late_charges'] > 0:
            param = self.env['ir.config_parameter'].sudo().search([('key', '=', 'asset_finance.penalty_income_account_id')], limit=1)
            penalty_account = param.value if param else False
            if penalty_account:
                line_items.append((0, 0, {
                    'name': f'Settlement - Penalties - {self.agreement_no}',
                    'account_id': int(penalty_account),
                    'debit': 0,
                    'credit': settlement_info['balance_late_charges'],
                }))

        # Create settlement journal entry
        settlement_move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': payment_journal.id,
            'date': settlement_date,
            'ref': payment_ref or f'Early Settlement - {self.agreement_no}',
            'line_ids': line_items,
        })

        # Post the entry
        settlement_move.action_post()

        # Update contract status
        self.ac_status = 'closed'
        self.balance_late_charges = 0
        self.balance_misc_fee = 0

        # Mark all remaining installments as settled
        remaining_lines = self.line_ids.filtered(
            lambda l: l.date_due >= settlement_date and l.invoice_id.payment_state != 'paid'
        )
        for line in remaining_lines:
            if line.invoice_id:
                line.invoice_id.button_draft()
                line.invoice_id.button_cancel()

        # Log in chatter
        self.message_post(
            body=f"✅ Early Settlement Processed<br/>"
                 f"Settlement Amount: {self.currency_id.symbol}{settlement_info['settlement_amount']:,.2f}<br/>"
                 f"Outstanding Principal: {self.currency_id.symbol}{settlement_info['outstanding_principal']:,.2f}<br/>"
                 f"Rebate Fee: {self.currency_id.symbol}{settlement_info['rebate_amount']:,.2f}<br/>"
                 f"Unearned Interest Waived: {self.currency_id.symbol}{unearned_writeoff:,.2f}<br/>"
                 f"Date: {settlement_date}"
        )

        return settlement_move

    # --------------------------------------------------------
    # INTEREST RECOGNITION (MONTHLY)
    # --------------------------------------------------------

    def _cron_recognize_monthly_interest(self):
        """
        Cron job to recognize earned interest monthly
        Converts Unearned Interest to Earned Interest

        Accounting Entry (for each paid installment this month):
        Dr. Unearned Interest            [Interest Portion]
            Cr. Interest Income          [Interest Portion]
        """
        today = fields.Date.today()
        first_day_month = today.replace(day=1)

        # Find installments paid this month
        paid_lines = self.env['finance.contract.line'].search([
            ('paid_date', '>=', first_day_month),
            ('paid_date', '<=', today),
            ('interest_recognized', '=', False)
        ])

        if not paid_lines:
            return

        # Group by contract for efficient processing
        contracts = paid_lines.mapped('contract_id')

        for contract in contracts:
            contract_lines = paid_lines.filtered(lambda l: l.contract_id == contract)

            total_interest = sum(contract_lines.mapped('amount_interest'))

            if total_interest <= 0:
                continue

            # Create interest recognition journal entry
            journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', contract.env.company.id)
            ], limit=1)

            move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': journal.id,
                'date': today,
                'ref': f'Interest Recognition - {contract.agreement_no}',
                'line_ids': [
                    (0, 0, {
                        'name': f'Interest Earned - {contract.agreement_no}',
                        'account_id': contract.unearned_interest_account_id.id,
                        'debit': total_interest,
                        'credit': 0,
                    }),
                    (0, 0, {
                        'name': f'Interest Income - {contract.agreement_no}',
                        'account_id': contract.income_account_id.id,
                        'debit': 0,
                        'credit': total_interest,
                    }),
                ],
            })

            move.action_post()

            # Mark lines as recognized
            contract_lines.write({'interest_recognized': True})

            # Log
            contract.message_post(
                body=f"Interest recognized: {contract.currency_id.symbol}{total_interest:,.2f}"
            )
