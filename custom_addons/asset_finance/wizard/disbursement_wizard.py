from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FinanceDisbursementWizard(models.TransientModel):
    _name = 'finance.disbursement.wizard'
    _description = 'Disbursement Wizard'

    contract_id = fields.Many2one('finance.contract', string="Contract", required=True, readonly=True)
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
        res = super(FinanceDisbursementWizard, self).default_get(fields_list)
        context_id = self.env.context.get('active_id')
        if context_id:
            contract = self.env['finance.contract'].browse(context_id)
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

        # Get account configuration
        try:
            account_config = self.env['finance.account.config'].get_config()
        except UserError:
            raise UserError(
                "Finance Account Configuration not found. "
                "Please configure account mapping under Finance > Configuration > Account Mapping."
            )

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

        # 3. DEBIT: HP Debtors - Others Charges (for Processing Fee + GST)
        # This creates an AR for the processing fee that offsets the net payout
        if self.processing_fee > 0 or self.processing_fee_tax > 0:
            # Use configured HP Charges account
            if not account_config.hp_charges_account_id:
                raise UserError(
                    "HP Charges account not configured. "
                    "Please configure it under Finance > Configuration > Account Mapping."
                )

            total_charges = self.processing_fee + self.processing_fee_tax
            move_lines.append((0, 0, {
                'name': "Processing Fee + GST (AR)",
                'account_id': account_config.hp_charges_account_id.id,
                'debit': total_charges,
                'credit': 0.0,
                'partner_id': contract.hirer_id.id,
            }))

        # 4. CREDIT: Processing Fee Income
        if self.processing_fee > 0:
            # Use configured Processing Fee Income account
            if not account_config.processing_fee_income_account_id:
                raise UserError(
                    "Processing Fee Income account not configured. "
                    "Please configure it under Finance > Configuration > Account Mapping."
                )

            move_lines.append((0, 0, {
                'name': "Hire Purchase Processing Fee",
                'account_id': account_config.processing_fee_income_account_id.id,
                'debit': 0.0,
                'credit': self.processing_fee,
            }))

        # 5. CREDIT: GST Output Tax
        if self.processing_fee_tax > 0:
            # Use configured GST Output account
            if not account_config.gst_output_account_id:
                raise UserError(
                    "GST Output Tax account not configured. "
                    "Please configure it under Finance > Configuration > Account Mapping."
                )

            move_lines.append((0, 0, {
                'name': "GST on Processing Fee",
                'account_id': account_config.gst_output_account_id.id,
                'debit': 0.0,
                'credit': self.processing_fee_tax,
            }))

        # 6. CREDIT: Bank (Net Payout)
        if self.amount_net > 0:
            if not self.journal_id.default_account_id:
                raise UserError(f"Journal {self.journal_id.name} has no default account.")
                
            move_lines.append((0, 0, {
                'name': f"{name} - Net Payout to Dealer",
                'account_id': self.journal_id.default_account_id.id,
                'debit': 0.0,
                'credit': self.amount_net,
                'partner_id': contract.supplier_id.id,
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