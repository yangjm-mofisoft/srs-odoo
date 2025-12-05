from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Wizard for Early Settlement Quotation, 
# allowing calculation of settlement amounts and creation of settlement invoices.
# This wizard calculates: {Settlement} = {Future Principal} + {Arrears (Unpaid Invoices)} + {Penalty} + {Settlement Fee}
class FinanceSettlementWizard(models.TransientModel):
    _name = 'finance.settlement.wizard'
    _description = 'Early Settlement Quotation'

    contract_id = fields.Many2one('finance.contract', string="Contract", required=True, readonly=True)
    settlement_date = fields.Date(string="Settlement Date", default=fields.Date.context_today, required=True)
    
    # --- Calculated Values ---
    outstanding_principal = fields.Monetary(string="Future Principal", help="Sum of Principal for lines not yet billed")
    unearned_interest = fields.Monetary(string="Interest Rebate (Rule 78)", help="Interest saved by the customer")
    
    arrears_amount = fields.Monetary(string="Arrears (Invoiced)", help="Total unpaid invoices including interest")
    penalty_amount = fields.Monetary(string="Accrued Penalty")
    
    # --- Settlement Charges (Rules from Image) ---
    # Rule: 20% of Rebate
    rebate_fee_rate = fields.Float(string="Fee on Rebate (%)", default=20.0, help="Standard: 20% of Interest Rebate")
    rebate_fee_amount = fields.Monetary(string="Fee on Rebate", compute='_compute_fees', store=True)
    
    # Rule: 1% or 2% of Principal (You can change default)
    principal_fee_rate = fields.Float(string="Fee on Principal (%)", default=1.0, help="Standard: 1-2% of Outstanding Principal")
    principal_fee_amount = fields.Monetary(string="Fee on Principal", compute='_compute_fees', store=True)
    
    notice_in_lieu_fee = fields.Monetary(string="Notice in Lieu Fee", help="1 month interest if insufficient notice given")
    
    manual_fee = fields.Monetary(string="Other Fees")
    
    # --- Totals ---
    total_payable = fields.Monetary(string="Total Settlement Amount", compute='_compute_total')
    currency_id = fields.Many2one(related='contract_id.currency_id')

    @api.model
    def default_get(self, fields_list):
        res = super(FinanceSettlementWizard, self).default_get(fields_list)
        context_id = self.env.context.get('active_id')
        if context_id:
            contract = self.env['finance.contract'].browse(context_id)
            res.update({
                'contract_id': contract.id,
                'penalty_amount': contract.balance_late_charges,
            })
            
            # 1. Calculate Arrears (Invoiced but Unpaid)
            unpaid_invoices = self.env['account.move'].search([
                ('invoice_origin', '=', contract.agreement_no),
                ('state', '=', 'posted'),
                ('payment_state', '!=', 'paid')
            ])
            res['arrears_amount'] = sum(unpaid_invoices.mapped('amount_residual'))
            
            # 2. Calculate Future Principal & Rebate (Unbilled Lines)
            future_lines = contract.line_ids.filtered(lambda l: not l.invoice_id)
            res['outstanding_principal'] = sum(future_lines.mapped('amount_principal'))
            res['unearned_interest'] = sum(future_lines.mapped('amount_interest'))
            
        return res

    @api.depends('outstanding_principal', 'unearned_interest', 'rebate_fee_rate', 'principal_fee_rate')
    def _compute_fees(self):
        for rec in self:
            rec.rebate_fee_amount = rec.unearned_interest * (rec.rebate_fee_rate / 100.0)
            rec.principal_fee_amount = rec.outstanding_principal * (rec.principal_fee_rate / 100.0)

    @api.depends('outstanding_principal', 'arrears_amount', 'penalty_amount', 'rebate_fee_amount', 'principal_fee_amount', 'notice_in_lieu_fee', 'manual_fee')
    def _compute_total(self):
        for rec in self:
            rec.total_payable = (
                rec.outstanding_principal + 
                rec.arrears_amount + 
                rec.penalty_amount + 
                rec.rebate_fee_amount + 
                rec.principal_fee_amount + 
                rec.notice_in_lieu_fee + 
                rec.manual_fee
            )

    def action_confirm_settlement(self):
        self.ensure_one()
        contract = self.contract_id
        
        invoice_lines = []
        
        # 1. Outstanding Principal
        if self.outstanding_principal > 0:
            invoice_lines.append((0, 0, {
                'name': f"Early Settlement - Principal Balance ({contract.agreement_no})",
                'quantity': 1,
                'price_unit': self.outstanding_principal,
                'account_id': contract.asset_account_id.id, 
            }))
            
        # 2. Settlement Charges (Grouped)
        total_fees = self.rebate_fee_amount + self.principal_fee_amount + self.notice_in_lieu_fee + self.manual_fee
        if total_fees > 0:
            invoice_lines.append((0, 0, {
                'name': "Early Settlement Charges",
                'quantity': 1,
                'price_unit': total_fees,
                'account_id': contract.income_account_id.id, 
            }))
            
        # 3. Penalty
        if self.penalty_amount > 0:
             invoice_lines.append((0, 0, {
                'name': "Settlement Penalty / Late Charges",
                'quantity': 1,
                'price_unit': self.penalty_amount,
                'account_id': contract.income_account_id.id, 
            }))

        if not invoice_lines:
            raise UserError("Amount to invoice is zero.")

        # Create Invoice
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
        
        contract.message_post(body=f"Early Settlement Invoice {invoice.name} created for {self.total_payable}.")
        
        return {
            'name': 'Settlement Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }