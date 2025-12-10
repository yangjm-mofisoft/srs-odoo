from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import math

class FinanceContract(models.Model):
    _inherit = 'finance.contract'

    # --------------------------------------------------------
    # FINANCIAL CALCULATIONS & AMORTIZATION
    # --------------------------------------------------------

    @api.depends('cash_price', 'down_payment', 'int_rate_pa', 'no_of_inst')
    def _compute_financials(self):
        """Calculate loan amount, term charges, and balance hire"""
        for rec in self:
            rec.loan_amount = rec.cash_price - rec.down_payment
            months = rec.no_of_inst.months if rec.no_of_inst else 0
            interest = (rec.loan_amount * (rec.int_rate_pa / 100) * (months / 12)) if months else 0
            rec.term_charges = interest
            rec.balance_hire = rec.loan_amount + interest

    @api.depends('loan_amount', 'int_rate_pa', 'no_of_inst')
    def _compute_installment_amounts(self):
        """
        Automatically computes the installment amounts based on the annuity formula.
        The fields remain editable for manual overrides.
        """
        for rec in self:
            if rec.no_of_inst and rec.no_of_inst.months > 0 and rec.loan_amount > 0:
                n = rec.no_of_inst.months
                if rec.int_rate_pa > 0:
                    # Standard annuity formula for level payments
                    P = rec.loan_amount
                    # Monthly interest rate
                    r = (rec.int_rate_pa / 100) / 12

                    # M = P * [r(1+r)^n] / [(1+r)^n - 1]
                    try:
                        monthly_inst = P * (r * (1 + r)**n) / ((1 + r)**n - 1)
                    except ZeroDivisionError:
                        monthly_inst = rec.loan_amount / n
                else:
                    # No interest, just divide principal by number of installments
                    monthly_inst = rec.loan_amount / n

                rounded_inst = math.floor(monthly_inst)
                rec.first_inst_amount = rounded_inst
                rec.monthly_inst = rounded_inst
                if n > 1:
                    rec.last_inst_amount = rec.balance_hire - (rounded_inst * (n - 1))
                else:
                    rec.last_inst_amount = rec.balance_hire
            else:
                rec.monthly_inst = rec.first_inst_amount = rec.last_inst_amount = 0

    # --------------------------------------------------------
    # SCHEDULE GENERATION (RULE OF 78 & FLAT RATE)
    # --------------------------------------------------------

    def action_generate_schedule(self):
        """Generate amortization schedule with Rule of 78 or Flat Rate"""
        self.ensure_one()
        self.line_ids.unlink()

        if not self.no_of_inst or not self.monthly_inst:
            raise UserError(_("Please set Number of Installments and Monthly Installment amount."))

        # 1. Determine Start Date based on Payment Scheme
        start_date = self.first_due_date
        if not start_date:
            base_date = self.agreement_date or fields.Date.today()
            if self.payment_scheme == 'advance':
                # Front payment: Due immediately on agreement date
                start_date = base_date
            else:
                # Normal arrears: Due 1 month after
                start_date = base_date + relativedelta(months=1)

        lines = []

        # 2. Setup Variables for Calculation
        n = self.no_of_inst.months
        total_principal = self.loan_amount
        total_interest = self.term_charges
        monthly_inst = self.monthly_inst

        # Rule of 78 Denominator: Sum of Digits = n * (n + 1) / 2
        # Example: For 12 months, SOD = 78.
        sum_of_digits = (n * (n + 1)) / 2 if self.interest_method == 'rule78' else 0

        # Trackers for rounding adjustments
        allocated_principal = 0.0
        allocated_interest = 0.0

        for i in range(1, n + 1):
            date_due = start_date + relativedelta(months=i-1)

            # --- A. Interest Calculation ---
            if self.interest_method == 'rule78':
                # Rule of 78 Formula:
                # Interest_k = Total_Interest * (Remaining_Months / Sum_of_Digits)
                # For month 1 of 12, Remaining weight is 12. For month 12, it is 1.
                weight = n - i + 1
                interest_portion = total_interest * (weight / sum_of_digits)
            else:
                # Flat Rate: Evenly distributed
                interest_portion = total_interest / n

            # Rounding to 2 decimal places is crucial for currency
            interest_portion = round(interest_portion, 2)

            # --- B. Principal Calculation ---
            # Determine the installment amount for this specific line
            if i == 1:
                amount_total = self.first_inst_amount
            else:
                amount_total = self.monthly_inst

            principal_portion = monthly_inst - interest_portion

            # --- C. Final Installment Adjustment ---
            if i == n:
                principal_portion = total_principal - allocated_principal
                interest_portion = total_interest - allocated_interest
                amount_total = principal_portion + interest_portion

            # Append the line
            lines.append((0, 0, {
                'sequence': i,
                'date_due': date_due,
                'amount_principal': principal_portion,
                'amount_interest': interest_portion,
                'amount_total': amount_total,
            }))

            # Update trackers
            allocated_principal += principal_portion
            allocated_interest += interest_portion

        self.write({'line_ids': lines})

    # --------------------------------------------------------
    # INVOICE CREATION
    # --------------------------------------------------------

    def action_create_invoices(self):
        """Create customer invoices for due installments"""
        for rec in self:
            due_lines = rec.line_ids.filtered(lambda l: not l.invoice_id and l.date_due <= fields.Date.today())
            if not due_lines:
                raise UserError(_("No installments are due for invoicing today."))

            for line in due_lines:
                invoice_lines = []
                invoice_lines.append((0, 0, {
                    'name': f"Principal Repayment (Inst #{line.sequence})",
                    'quantity': 1,
                    'price_unit': line.amount_principal,
                    'account_id': rec.asset_account_id.id,
                }))

                if line.amount_interest > 0:
                    invoice_lines.append((0, 0, {
                        'name': f"Interest Charges (Inst #{line.sequence})",
                        'quantity': 1,
                        'price_unit': line.amount_interest,
                        'account_id': rec.income_account_id.id,
                        'tax_ids': []
                    }))

                invoice = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': rec.hirer_id.id,
                    'invoice_date': line.date_due,
                    'date': line.date_due,
                    'journal_id': rec.journal_id.id,
                    'invoice_origin': rec.agreement_no, # Used for invoice stat button
                    'ref': f"Installment {line.sequence}/{rec.no_of_inst.months}",
                    'invoice_line_ids': invoice_lines,
                })

                line.invoice_id = invoice.id
                invoice.action_post()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Success', 'message': f'{len(due_lines)} Invoices created!', 'type': 'success'}
            }

    # --------------------------------------------------------
    # EARLY SETTLEMENT CALCULATIONS
    # --------------------------------------------------------

    def action_early_settlement(self):
        """Open Early Settlement Wizard"""
        self.ensure_one()
        return {
            'name': 'Early Settlement',
            'type': 'ir.actions.act_window',
            'res_model': 'finance.settlement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id, 'active_id': self.id}
        }

    def calculate_settlement_amount(self, settlement_date):
        """
        Calculate early settlement amount using Rule of 78 rebate
        Returns: {
            'outstanding_principal': float,
            'unearned_interest': float,
            'rebate_amount': float,
            'settlement_amount': float
        }
        """
        self.ensure_one()

        # Get configuration parameters
        rebate_fee_pct = float(self.env['ir.config_parameter'].sudo().get_param(
            'asset_finance.settlement_rebate_fee', default=20.0))

        # Find remaining unpaid installments
        remaining_lines = self.line_ids.filtered(
            lambda l: l.date_due >= settlement_date and l.invoice_id.payment_state != 'paid'
        )

        outstanding_principal = sum(remaining_lines.mapped('amount_principal'))
        unearned_interest = sum(remaining_lines.mapped('amount_interest'))

        # Calculate rebate (typically 20% of unearned interest is charged)
        rebate_amount = unearned_interest * (rebate_fee_pct / 100)

        # Settlement = Outstanding Principal + Rebate + Penalties + Misc Fees
        settlement_amount = outstanding_principal + rebate_amount + \
                          self.balance_late_charges + self.balance_misc_fee

        return {
            'outstanding_principal': outstanding_principal,
            'unearned_interest': unearned_interest,
            'rebate_amount': rebate_amount,
            'settlement_amount': settlement_amount,
            'balance_late_charges': self.balance_late_charges,
            'balance_misc_fee': self.balance_misc_fee
        }
