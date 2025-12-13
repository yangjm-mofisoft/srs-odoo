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
            raise UserError(_("Disbursement already created for this contract."))

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
        Legacy helper kept for tests – now routes through account.payment
        """
        self.ensure_one()

        if self.disbursement_move_id:
            raise UserError(_("Disbursement already processed!"))

        journal = self.env['account.journal'].browse(payment_method_id)
        if not journal:
            raise UserError(_("Please pass a valid bank journal ID to create the disbursement payment."))

        payment_method_line = journal.outbound_payment_method_line_ids[:1]
        if not payment_method_line:
            raise UserError(_("Journal %s has no outbound payment method configured.") % journal.display_name)

        net_amount = self.loan_amount - self.commission - self.admin_fee
        payment_vals = {
            'payment_type': 'outbound',
            'partner_type': 'supplier' if self.supplier_id else 'customer',
            'partner_id': (self.supplier_id or self.hirer_id).id,
            'amount': net_amount,
            'currency_id': self.currency_id.id,
            'date': disbursement_date,
            'journal_id': journal.id,
            'payment_method_line_id': payment_method_line.id,
            'ref': f"Disbursement {self.agreement_no}",
            'contract_id': self.id,
            'is_finance_disbursement': True,
            'disbursement_principal': self.loan_amount,
            'disbursement_interest': self.term_charges,
            'disbursement_processing_fee': 0.0,
            'disbursement_processing_fee_tax': 0.0,
            'disbursement_advance_payment': 0.0,
            'disbursement_admin_fee': self.admin_fee,
            'disbursement_commission': self.commission,
        }

        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        self.disbursement_payment_id = payment.id
        self.disbursement_move_id = payment.move_id.id
        self.ac_status = 'active'

        self.message_post(
            body=f"Disbursement Payment created: {payment.name}<br/>"
                 f"Net Amount: {self.currency_id.symbol}{net_amount:,.2f}<br/>"
                 f"Date: {disbursement_date}"
        )

        return payment.move_id

    def action_view_disbursement(self):
        """Open the disbursement payment/move"""
        self.ensure_one()
        if not self.disbursement_move_id:
            raise UserError(_("No disbursement entry found for this contract."))

        if self.disbursement_payment_id:
            return {
                'name': _('Disbursement Payment'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': self.disbursement_payment_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

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
            journal_param = self.env['ir.config_parameter'].sudo().get_param('asset_finance.interest_recognition_journal_id')
            journal = self.env['account.journal'].browse(int(journal_param)) if journal_param and journal_param != 'False' else False
            if not journal:
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
