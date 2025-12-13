from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round
from dateutil.relativedelta import relativedelta
import math

class FinanceContract(models.Model):
    _inherit = 'finance.contract'

    # --------------------------------------------------------
    # FINANCIAL CALCULATIONS & AMORTIZATION
    # --------------------------------------------------------

    @api.depends('cash_price', 'down_payment', 'int_rate_pa', 'no_of_inst', 'interest_type')
    def _compute_financials(self):
        """
        Calculate loan amount and, for flat rate loans, the term charges and balance hire.
        For effective rate (annuity) loans, term charges and balance hire are determined by the schedule.
        """
        for rec in self:
            rec.loan_amount = rec.cash_price - rec.down_payment
            if rec.interest_type == 'flat':
                months = rec.no_of_inst.months if rec.no_of_inst else 0
                interest = (rec.loan_amount * (rec.int_rate_pa / 100) * (months / 12)) if months else 0
                rec.term_charges = interest
                rec.balance_hire = rec.loan_amount + interest
            else: # effective rate
                # For effective rate, these are placeholders until schedule is generated
                rec.term_charges = 0.0
                rec.balance_hire = rec.loan_amount

    @api.depends('loan_amount', 'int_rate_pa', 'no_of_inst', 'interest_type', 'balance_hire')
    def _compute_installment_amounts(self):
        """
        Automatically computes a proposed installment amount.
        - For 'effective' rate, it uses the annuity formula.
        - For 'flat' rate, it uses simple division of the total balance hire.
        """
        for rec in self:
            if rec.no_of_inst and rec.no_of_inst.months > 0 and rec.loan_amount > 0:
                n = rec.no_of_inst.months
                monthly_inst = 0.0

                if rec.interest_type == 'effective':
                    if rec.int_rate_pa > 0:
                        P = rec.loan_amount
                        r = (rec.int_rate_pa / 100) / 12  # Monthly interest rate
                        try:
                            # M = P * [r(1+r)^n] / [(1+r)^n - 1]
                            monthly_inst = P * (r * (1 + r)**n) / ((1 + r)**n - 1)
                        except (ValueError, ZeroDivisionError):
                            monthly_inst = rec.loan_amount / n
                    else:
                        monthly_inst = rec.loan_amount / n
                
                elif rec.interest_type == 'flat':
                    if n > 0 and rec.balance_hire > 0:
                        monthly_inst = rec.balance_hire / n

                rounded_inst = float_round(monthly_inst, precision_digits=rec.currency_id.decimal_places)
                rec.first_inst_amount = rounded_inst
                rec.monthly_inst = rounded_inst
                # For flat rate, the last installment must absorb rounding differences
                if rec.interest_type == 'flat' and n > 1:
                     rec.last_inst_amount = rec.balance_hire - (rounded_inst * (n - 1))
                else:
                     rec.last_inst_amount = rounded_inst
            else:
                rec.monthly_inst = rec.first_inst_amount = rec.last_inst_amount = 0

    # --------------------------------------------------------
    # SCHEDULE GENERATION
    # --------------------------------------------------------

    def action_generate_schedule(self):
        """Generate amortization schedule based on the selected Interest Type."""
        for rec in self:
            if rec.interest_type == 'effective':
                rec._generate_schedule_effective()
            elif rec.interest_type == 'flat':
                rec._generate_schedule_flat()

    def _generate_schedule_flat(self):
        """Generates a schedule by evenly distributing pre-calculated total interest."""
        self.ensure_one()
        self.line_ids.unlink()
        if not self.no_of_inst or self.no_of_inst.months <= 0:
            raise UserError(_("Please set a valid Number of Installments."))
        if self.monthly_inst <= 0:
             raise UserError(_("Please set a valid Monthly Installment amount."))

        start_date = self.first_due_date or (self.agreement_date or fields.Date.today()) + relativedelta(months=1)
        lines = []
        precision = self.currency_id.decimal_places

        n = self.no_of_inst.months
        total_principal = self.loan_amount
        total_interest = self.term_charges # Pre-calculated for flat rate

        allocated_principal = 0.0
        allocated_interest = 0.0

        for i in range(1, n + 1):
            date_due = start_date + relativedelta(months=i - 1)
            
            # Use the stored installment amounts
            amount_total = self.monthly_inst
            if i == 1: amount_total = self.first_inst_amount
            elif i == n: amount_total = self.last_inst_amount

            # Distribute interest evenly as a baseline
            interest_portion = float_round(total_interest / n, precision_digits=precision)
            principal_portion = amount_total - interest_portion

            # Final installment adjustment to absorb rounding differences
            if i == n:
                principal_portion = total_principal - allocated_principal
                interest_portion = total_interest - allocated_interest
                amount_total = principal_portion + interest_portion

            lines.append((0, 0, {
                'sequence': i, 'date_due': date_due,
                'amount_principal': principal_portion,
                'amount_interest': interest_portion,
                'amount_total': amount_total,
            }))

            allocated_principal += principal_portion
            allocated_interest += interest_portion
        
        self.write({'line_ids': lines})

    def _generate_schedule_effective(self):
        """Generate a standard amortization schedule based on annuity calculation."""
        self.ensure_one()
        self.line_ids.unlink()
        if not self.no_of_inst or self.no_of_inst.months <= 0:
            raise UserError(_("Please set a valid Number of Installments."))
        if self.monthly_inst <= 0:
            raise UserError(_("Please set a valid Monthly Installment amount."))


        start_date = self.first_due_date or (self.agreement_date or fields.Date.today()) + relativedelta(months=1)
        lines = []
        precision = self.currency_id.decimal_places

        n = self.no_of_inst.months
        p = self.loan_amount
        r = (self.int_rate_pa / 100) / 12 if self.int_rate_pa > 0 else 0
        
        remaining_principal = p
        total_interest_calculated = 0.0

        for i in range(1, n + 1):
            date_due = start_date + relativedelta(months=i - 1)
            
            inst_amount = self.monthly_inst
            if i == 1: inst_amount = self.first_inst_amount
            elif i == n: inst_amount = self.last_inst_amount

            interest_portion = float_round(remaining_principal * r, precision_digits=precision)
            
            # On the last installment, ensure all remaining principal is paid off
            if i == n:
                principal_portion = remaining_principal
                inst_amount = principal_portion + interest_portion
            else:
                principal_portion = inst_amount - interest_portion
            
            lines.append((0, 0, {
                'sequence': i, 'date_due': date_due,
                'amount_principal': principal_portion,
                'amount_interest': interest_portion,
                'amount_total': inst_amount,
            }))

            remaining_principal -= principal_portion
            total_interest_calculated += interest_portion

        total_repayment = self.loan_amount + total_interest_calculated
        self.write({
            'line_ids': lines,
            'term_charges': total_interest_calculated,
            'balance_hire': total_repayment,
        })

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
                    'invoice_origin': rec.agreement_no,
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
        Calculate early settlement amount based on the contract's interest type.
        """
        self.ensure_one()

        remaining_lines = self.line_ids.filtered(
            lambda l: l.date_due >= settlement_date and (not l.invoice_id or l.invoice_id.payment_state != 'paid')
        )

        outstanding_principal = sum(remaining_lines.mapped('amount_principal'))
        unearned_interest = sum(remaining_lines.mapped('amount_interest'))
        
        settlement_amount = 0
        rebate_amount = 0.0
        interest_rebate = 0.0

        if self.interest_type == 'effective':
            # For annuity, settlement is simply the outstanding principal plus any fees.
            settlement_amount = outstanding_principal + self.balance_late_charges + self.balance_misc_fee
        
        elif self.interest_type == 'flat':
            # For flat rate, a rebate on unearned interest is typically given.
            param = self.env['ir.config_parameter'].sudo().get_param('asset_finance.settlement_rebate_fee_pct', 20.0)
            rebate_fee_pct = float(param)
            
            # The fee is the portion of unearned interest that the finance company keeps.
            rebate_amount = unearned_interest * (rebate_fee_pct / 100)
            # The rebate is the portion returned to the customer.
            interest_rebate = unearned_interest - rebate_amount
            
            settlement_amount = outstanding_principal + rebate_amount + self.balance_late_charges + self.balance_misc_fee

        result = {
            'outstanding_principal': outstanding_principal,
            'unearned_interest': unearned_interest,
            'settlement_amount': settlement_amount,
            'balance_late_charges': self.balance_late_charges,
            'balance_misc_fee': self.balance_misc_fee,
            'rebate_amount': rebate_amount,
            'interest_rebate': interest_rebate,
            'rebate_fee': rebate_amount,  # backward compatibility
        }
        return result
