from odoo import models, fields, api, _
from odoo.exceptions import UserError

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

        return res

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