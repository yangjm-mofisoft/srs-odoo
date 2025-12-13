from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Link the Payment to a Contract
    contract_id = fields.Many2one('finance.contract', string="Finance Contract", readonly=True)

    # Optional: Display vehicle info on the payment for easier search
    asset_reg_no = fields.Char(related='contract_id.asset_reg_no', string="Asset Reg", store=True)

    # Payment Allocation Details
    payment_allocation_ids = fields.One2many('finance.payment.allocation', 'payment_id', string="Payment Allocation")
    allocated_to_penalties = fields.Monetary(string="Allocated to Penalties", compute='_compute_allocations', store=True)
    allocated_to_principal = fields.Monetary(string="Allocated to Principal", compute='_compute_allocations', store=True)
    allocated_to_interest = fields.Monetary(string="Allocated to Interest", compute='_compute_allocations', store=True)

    is_finance_disbursement = fields.Boolean(string="Asset Finance Disbursement", default=False)
    disbursement_principal = fields.Monetary(string="Disbursement Principal", currency_field='currency_id')
    disbursement_interest = fields.Monetary(string="Disbursement Interest", currency_field='currency_id')
    disbursement_processing_fee = fields.Monetary(string="Processing Fee", currency_field='currency_id')
    disbursement_processing_fee_tax = fields.Monetary(string="Processing Fee Tax", currency_field='currency_id')
    disbursement_advance_payment = fields.Monetary(string="Advance Installment Deduction", currency_field='currency_id')
    disbursement_admin_fee = fields.Monetary(string="Admin Fee", currency_field='currency_id')
    disbursement_commission = fields.Monetary(string="Supplier Commission", currency_field='currency_id')

    @api.depends('payment_allocation_ids.amount')
    def _compute_allocations(self):
        for payment in self:
            payment.allocated_to_penalties = sum(payment.payment_allocation_ids.filtered(lambda a: a.allocation_type == 'penalty').mapped('amount'))
            payment.allocated_to_principal = sum(payment.payment_allocation_ids.filtered(lambda a: a.allocation_type == 'principal').mapped('amount'))
            payment.allocated_to_interest = sum(payment.payment_allocation_ids.filtered(lambda a: a.allocation_type == 'interest').mapped('amount'))

    def action_post(self):
        """Override to allocate payment to contract when posted"""
        res = super(AccountPayment, self).action_post()

        for payment in self:
            if payment.contract_id and payment.payment_type == 'inbound':
                payment._allocate_payment_to_contract()
            if payment.is_finance_disbursement and payment.contract_id:
                payment.contract_id.disbursement_payment_id = payment.id
                payment.contract_id.disbursement_move_id = payment.move_id.id
                payment.contract_id.message_post(
                    body=_("Disbursement Payment %s posted for %s.")
                         % (payment.name, payment.contract_id.agreement_no)
                )

        return res

    def _prepare_payment_moves(self):
        moves = super()._prepare_payment_moves()
        for payment, move_vals in zip(self, moves):
            if not payment.is_finance_disbursement:
                continue
            line_vals = payment._prepare_finance_disbursement_move_lines()
            move_vals['line_ids'] = line_vals
            move_vals['move_type'] = 'entry'
        return moves

    def _prepare_finance_disbursement_move_lines(self):
        self.ensure_one()
        contract = self.contract_id
        if not contract:
            raise UserError(_("Finance disbursement payments must be linked to a contract."))
        if not contract.asset_account_id or not contract.unearned_interest_account_id:
            raise UserError(_("Please configure the asset and unearned interest accounts on the contract."))

        account_config = self.env['finance.account.config'].get_config()

        partner_hirer = contract.hirer_id
        partner_supplier = self.partner_id

        amount_principal = self.disbursement_principal
        amount_interest = self.disbursement_interest
        processing_fee = self.disbursement_processing_fee
        processing_fee_tax = self.disbursement_processing_fee_tax
        advance_payment = self.disbursement_advance_payment
        admin_fee = self.disbursement_admin_fee
        commission = self.disbursement_commission

        gross_amount = amount_principal + amount_interest
        total_charges = processing_fee + processing_fee_tax

        lines = []
        currency = self.currency_id or self.company_id.currency_id

        def _line(name, account, debit=0.0, credit=0.0, partner=False):
            vals = {
                'name': name,
                'account_id': account.id,
                'debit': debit,
                'credit': credit,
                'partner_id': partner.id if partner else False,
            }
            if currency and currency != self.company_id.currency_id:
                vals.update({
                    'currency_id': currency.id,
                    'amount_currency': debit - credit,
                })
            return (0, 0, vals)

        lines.append(_line(
            _("Disbursement - Principal & Interest %s") % contract.agreement_no,
            contract.asset_account_id,
            debit=gross_amount,
            partner=partner_hirer
        ))

        if amount_interest:
            lines.append(_line(
                _("Unearned Interest %s") % contract.agreement_no,
                contract.unearned_interest_account_id,
                credit=amount_interest
            ))

        if total_charges:
            if not account_config.hp_charges_account_id:
                raise UserError(_("HP Charges account is not configured."))
            lines.append(_line(
                _("Processing Fee + Tax AR"),
                account_config.hp_charges_account_id,
                debit=total_charges,
                partner=partner_hirer
            ))

        if processing_fee:
            if not account_config.processing_fee_income_account_id:
                raise UserError(_("Processing Fee Income account is not configured."))
            lines.append(_line(
                _("Processing Fee Income"),
                account_config.processing_fee_income_account_id,
                credit=processing_fee
            ))

        if processing_fee_tax:
            if not account_config.gst_output_account_id:
                raise UserError(_("GST Output account is not configured."))
            lines.append(_line(
                _("GST on Processing Fee"),
                account_config.gst_output_account_id,
                credit=processing_fee_tax
            ))

        if admin_fee:
            admin_fee_account_id = self.env['ir.config_parameter'].sudo().get_param('asset_finance.admin_fee_account_id')
            if not admin_fee_account_id or admin_fee_account_id == 'False':
                raise UserError(_("Admin fee account is not configured in settings."))
            admin_fee_account = self.env['account.account'].browse(int(admin_fee_account_id))
            lines.append(_line(
                _("Admin Fee Expense"),
                admin_fee_account,
                debit=admin_fee
            ))

        if commission and contract.supplier_id:
            commission_account = contract.supplier_id.property_account_payable_id
            if not commission_account:
                raise UserError(_("Supplier %s is missing a payable account.") % contract.supplier_id.display_name)
            lines.append(_line(
                _("Supplier Commission"),
                commission_account,
                credit=commission,
                partner=contract.supplier_id
            ))

        liquidity_account = self.journal_id.default_account_id
        if not liquidity_account:
            raise UserError(_("Journal %s has no default account configured.") % self.journal_id.display_name)

        lines.append(_line(
            _("Net Payout %s") % contract.agreement_no,
            liquidity_account,
            credit=self.amount,
            partner=partner_supplier
        ))

        total_debit = sum(l[2]['debit'] for l in lines)
        total_credit = sum(l[2]['credit'] for l in lines)
        diff = total_debit - total_credit
        if not float_is_zero(diff, precision_rounding=self.currency_id.rounding if self.currency_id else self.company_id.currency_id.rounding):
            lines.append(_line(
                _("Advance/Adjustment"),
                contract.asset_account_id,
                credit=diff if diff > 0 else 0.0,
                debit=-diff if diff < 0 else 0.0,
                partner=partner_hirer
            ))

        return lines

    def _allocate_payment_to_contract(self):
        """
        Allocate payment to contract following waterfall logic:
        1. Penalties (oldest first)
        2. Overdue installments (oldest first)
        3. Current installments
        """
        self.ensure_one()
        contract = self.contract_id
        remaining_amount = self.amount
        allocation_lines = []

        # Step 1: Allocate to Penalties first
        if contract.balance_late_charges > 0:
            penalty_amount = min(remaining_amount, contract.balance_late_charges)
            allocation_lines.append((0, 0, {
                'payment_id': self.id,
                'contract_line_id': False,
                'allocation_type': 'penalty',
                'amount': penalty_amount,
            }))
            remaining_amount -= penalty_amount
            contract.total_late_paid += penalty_amount
            contract.balance_late_charges -= penalty_amount

        # Step 2 & 3: Allocate to Installments (overdue first, then current)
        if remaining_amount > 0:
            # Find unpaid/partially paid installments (oldest first)
            unpaid_lines = contract.line_ids.filtered(
                lambda l: l.invoice_id and l.invoice_id.payment_state in ['not_paid', 'partial']
            ).sorted('date_due')

            for line in unpaid_lines:
                if remaining_amount <= 0:
                    break

                # Calculate remaining on this line
                line_remaining = line.amount_total
                if line.invoice_id:
                    line_remaining = line.invoice_id.amount_residual

                if line_remaining > 0:
                    line_payment = min(remaining_amount, line_remaining)

                    # Split between principal and interest based on invoice lines
                    principal_ratio = line.amount_principal / line.amount_total if line.amount_total > 0 else 0
                    interest_ratio = line.amount_interest / line.amount_total if line.amount_total > 0 else 0

                    principal_allocated = line_payment * principal_ratio
                    interest_allocated = line_payment * interest_ratio

                    # Create allocation records
                    allocation_lines.append((0, 0, {
                        'payment_id': self.id,
                        'contract_line_id': line.id,
                        'allocation_type': 'principal',
                        'amount': principal_allocated,
                    }))

                    allocation_lines.append((0, 0, {
                        'payment_id': self.id,
                        'contract_line_id': line.id,
                        'allocation_type': 'interest',
                        'amount': interest_allocated,
                    }))

                    remaining_amount -= line_payment

        # Write all allocations at once
        if allocation_lines:
            self.payment_allocation_ids = allocation_lines

        # Log allocation in chatter
        if contract:
            message = f"Payment {self.name} of {self.amount} allocated:<br/>"
            message += f"- Penalties: {self.allocated_to_penalties}<br/>"
            message += f"- Principal: {self.allocated_to_principal}<br/>"
            message += f"- Interest: {self.allocated_to_interest}"
            contract.message_post(body=message)


class FinancePaymentAllocation(models.Model):
    _name = 'finance.payment.allocation'
    _description = 'Payment Allocation Line'
    _order = 'payment_id, id'

    payment_id = fields.Many2one('account.payment', string="Payment", required=True, ondelete='cascade')
    contract_line_id = fields.Many2one('finance.contract.line', string="Installment Line")
    allocation_type = fields.Selection([
        ('penalty', 'Penalty'),
        ('principal', 'Principal'),
        ('interest', 'Interest')
    ], string="Type", required=True)
    amount = fields.Monetary(string="Amount", required=True)
    currency_id = fields.Many2one(related='payment_id.currency_id')
