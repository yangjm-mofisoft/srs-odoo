from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Wizard for Early Settlement Quotation, 
# allowing calculation of settlement amounts and creation of settlement invoices.
# This wizard calculates: {Settlement} = {Future Principal} + {Arrears (Unpaid Invoices)} + {Penalty} + {Settlement Fee}
class LeasingSettlementWizard(models.TransientModel):
    _name = 'leasing.settlement.wizard'
    _description = 'Early Settlement Quotation'

    contract_id = fields.Many2one('leasing.contract', string="Contract", required=True, readonly=True)
    settlement_date = fields.Date(string="Settlement Date", default=fields.Date.context_today, required=True)
    
    # --- Calculated Values ---
    outstanding_principal = fields.Monetary(string="Future Principal", help="Sum of Principal for lines not yet billed")
    unearned_interest = fields.Monetary(string="Interest Rebate", help="Interest you are saving the customer (Info only)")
    
    arrears_amount = fields.Monetary(string="Arrears (Invoiced)", help="Total unpaid invoices including interest")
    penalty_amount = fields.Monetary(string="Accrued Penalty")
    
    # --- Fees ---
    settlement_fee = fields.Monetary(string="Settlement Fee")
    
    # --- Totals ---
    total_payable = fields.Monetary(string="Total Settlement Amount", compute='_compute_total')
    currency_id = fields.Many2one(related='contract_id.currency_id')

    @api.model
    def default_get(self, fields_list):
        res = super(LeasingSettlementWizard, self).default_get(fields_list)
        context_id = self.env.context.get('active_id')
        if context_id:
            contract = self.env['leasing.contract'].browse(context_id)
            res.update({
                'contract_id': contract.id,
                'penalty_amount': contract.balance_late_charges, # Uses the field we added in the previous step
            })
            
            # 1. Calculate Arrears (Invoiced but Unpaid)
            unpaid_invoices = self.env['account.move'].search([
                ('invoice_origin', '=', contract.agreement_no),
                ('state', '=', 'posted'),
                ('payment_state', '!=', 'paid')
            ])
            res['arrears_amount'] = sum(unpaid_invoices.mapped('amount_residual'))
            
            # 2. Calculate Future Principal (Unbilled Lines)
            # We look for lines that DO NOT have an invoice_id yet
            future_lines = contract.line_ids.filtered(lambda l: not l.invoice_id)
            res['outstanding_principal'] = sum(future_lines.mapped('amount_principal'))
            res['unearned_interest'] = sum(future_lines.mapped('amount_interest'))
            
        return res

    @api.depends('outstanding_principal', 'arrears_amount', 'penalty_amount', 'settlement_fee')
    def _compute_total(self):
        for rec in self:
            rec.total_payable = (
                rec.outstanding_principal + 
                rec.arrears_amount + 
                rec.penalty_amount + 
                rec.settlement_fee
            )

    def action_confirm_settlement(self):
        """
        1. Create an Invoice for the Future Principal + Settlement Fee.
        2. (Optional) Create a separate invoice for Penalty if not already billed.
        3. Close the contract or mark as 'In Settlement'.
        """
        self.ensure_one()
        contract = self.contract_id
        
        invoice_lines = []
        
        # Line 1: Outstanding Principal
        if self.outstanding_principal > 0:
            invoice_lines.append((0, 0, {
                'name': f"Early Settlement - Principal Balance ({contract.agreement_no})",
                'quantity': 1,
                'price_unit': self.outstanding_principal,
                'account_id': contract.asset_account_id.id, 
            }))
            
        # Line 2: Settlement Fee
        if self.settlement_fee > 0:
            # You might want a specific income account for fees. 
            # For now, using the general income account from contract.
            invoice_lines.append((0, 0, {
                'name': "Early Settlement Fee",
                'quantity': 1,
                'price_unit': self.settlement_fee,
                'account_id': contract.income_account_id.id, 
            }))
            
        # Line 3: Penalty (if you want to bill it now)
        if self.penalty_amount > 0:
             invoice_lines.append((0, 0, {
                'name': "Settlement Penalty / Late Charges",
                'quantity': 1,
                'price_unit': self.penalty_amount,
                'account_id': contract.income_account_id.id, 
            }))

        if not invoice_lines:
            raise UserError("Amount to invoice is zero. Cannot create settlement invoice.")

        # Create the Settlement Invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': contract.hirer_id.id,
            'invoice_date': self.settlement_date,
            'journal_id': contract.journal_id.id,
            'invoice_origin': contract.agreement_no,
            'ref': "Early Settlement",
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_post()
        
        # Update Contract Status
        # We don't close it immediately; we wait for payment.
        # But we can mark it as 'legal' or a new state 'settlement' if you added one.
        # For now, we leave it active but post a message.
        contract.message_post(body=f"Early Settlement Invoice {invoice.name} created for {self.total_payable}.")
        
        # Open the new Invoice
        return {
            'name': 'Settlement Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }