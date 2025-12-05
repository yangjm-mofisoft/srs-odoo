from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LeasingDisbursementWizard(models.TransientModel):
    _name = 'leasing.disbursement.wizard'
    _description = 'Disbursement Wizard'

    contract_id = fields.Many2one('leasing.contract', string="Contract", required=True, readonly=True)
    journal_id = fields.Many2one('account.journal', string="Bank Journal", domain=[('type', 'in', ['bank', 'cash'])], required=True)
    disbursement_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)

    # --- Amounts ---
    amount_principal = fields.Monetary(string="Loan Amount (Principal)")
    amount_interest = fields.Monetary(string="Total Interest")
    amount_gross = fields.Monetary(string="Gross Amount (P+I)", compute='_compute_gross')
    
    # --- Deductions ---
    processing_fee = fields.Monetary(string="Processing Fee")
    processing_fee_tax = fields.Monetary(string="Processing Fee GST")
    advance_payment = fields.Monetary(string="Advance Installment (Arrears)")
    
    # --- Net Payout ---
    amount_net = fields.Monetary(string="Net Payout Amount", compute='_compute_net')
    
    currency_id = fields.Many2one(related='contract_id.currency_id')

    @api.model
    def default_get(self, fields_list):
        res = super(LeasingDisbursementWizard, self).default_get(fields_list)
        context_id = self.env.context.get('active_id')
        if context_id:
            contract = self.env['leasing.contract'].browse(context_id)
            res.update({
                'contract_id': contract.id,
                'amount_principal': contract.loan_amount,
                'amount_interest': contract.term_charges,
                # Pre-fill fees if fields exist on contract, else 0
                'processing_fee': contract.admin_fee or 0.0,
            })
        return res

    @api.depends('amount_principal', 'amount_interest')
    def _compute_gross(self):
        for rec in self:
            rec.amount_gross = rec.amount_principal + rec.amount_interest

    @api.depends('amount_principal', 'processing_fee', 'processing_fee_tax', 'advance_payment')
    def _compute_net(self):
        for rec in self:
            # Net Payout = Principal - Fees - Advance
            # (Note: Interest is booked to Unearned, not paid out)
            rec.amount_net = rec.amount_principal - rec.processing_fee - rec.processing_fee_tax - rec.advance_payment

    def action_confirm_disbursement(self):
        self.ensure_one()
        contract = self.contract_id
        
        if not contract.asset_account_id or not contract.unearned_interest_account_id:
            raise UserError("Please configure the Asset and Unearned Interest accounts on the Contract.")

        move_lines = []
        name = f"Disbursement for {contract.agreement_no}"

        # 1. DEBIT: HP Debtors (Gross Amount: Principal + Interest)
        move_lines.append((0, 0, {
            'name': f"{name} - HP Debtors (Gross)",
            'account_id': contract.asset_account_id.id,
            'debit': self.amount_gross,
            'credit': 0.0,
            'partner_id': contract.hirer_id.id,
        }))

        # 2. CREDIT: Unearned Interest (Interest Portion)
        move_lines.append((0, 0, {
            'name': f"{name} - Unearned Interest",
            'account_id': contract.unearned_interest_account_id.id,
            'debit': 0.0,
            'credit': self.amount_interest,
        }))

        # 3. CREDIT: Processing Fee Income (Deduction)
        if self.processing_fee > 0:
            # Fallback to contract Income account if specific fee account is missing
            fee_account = contract.income_account_id.id
            move_lines.append((0, 0, {
                'name': "Processing Fee",
                'account_id': fee_account,
                'debit': 0.0,
                'credit': self.processing_fee,
            }))

        # 4. CREDIT: GST Output (Deduction)
        if self.processing_fee_tax > 0:
            # Find a default tax account or use system default
            # For simplicity using income account, but should be tax payable
            move_lines.append((0, 0, {
                'name': "GST on Processing Fee",
                'account_id': contract.income_account_id.id, # Ideally separate tax account
                'debit': 0.0,
                'credit': self.processing_fee_tax,
            }))

        # 5. CREDIT: Bank (Net Payout)
        if self.amount_net > 0:
            if not self.journal_id.default_account_id:
                raise UserError(f"Journal {self.journal_id.name} has no default account.")
                
            move_lines.append((0, 0, {
                'name': f"{name} - Net Payout to Dealer",
                'account_id': self.journal_id.default_account_id.id,
                'debit': 0.0,
                'credit': self.amount_net,
                'partner_id': contract.dealer_partner_id.id,
            }))

        # Validation: Check balance
        total_deb = sum(l[2]['debit'] for l in move_lines)
        total_cred = sum(l[2]['credit'] for l in move_lines)
        if round(total_deb, 2) != round(total_cred, 2):
             # Add a balancing line for Advance Payment if needed
             # If Advance Payment was deducted, we credit the Asset Account (Installment Contra)
             diff = total_deb - total_cred
             if self.advance_payment > 0 and abs(diff - self.advance_payment) < 0.01:
                 move_lines.append((0, 0, {
                    'name': "Advance Installment Deduction",
                    'account_id': contract.asset_account_id.id, # Crediting the debtor
                    'debit': 0.0,
                    'credit': diff,
                 }))

        # Create Journal Entry
        move = self.env['account.move'].create({
            'ref': name,
            'date': self.disbursement_date,
            'journal_id': self.journal_id.id,
            'move_type': 'entry',
            'line_ids': move_lines,
        })
        move.action_post()

        # Link to Contract
        contract.disbursement_move_id = move.id
        
        return {
            'name': 'Disbursement Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
        }