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
            journal_param = self.env['ir.config_parameter'].sudo().get_param('asset_finance.disbursement_journal_id')
            if journal_param and journal_param != 'False':
                res['journal_id'] = int(journal_param)
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
        if contract.disbursement_move_id:
            raise UserError(_("Disbursement already processed for this contract."))

        if not contract.asset_account_id or not contract.unearned_interest_account_id:
            raise UserError(_("Please configure the Asset and Unearned Interest accounts on the contract."))

        journal = self.journal_id
        payment_method_line = journal.outbound_payment_method_line_ids[:1]
        if not payment_method_line:
            raise UserError(_("Journal %s has no outbound payment method configured.") % journal.display_name)

        partner = contract.supplier_id or contract.hirer_id
        if not partner:
            raise UserError(_("Please set a supplier or hirer partner on the contract."))

        payment_vals = {
            'payment_type': 'outbound',
            'partner_type': 'supplier' if partner == contract.supplier_id else 'customer',
            'partner_id': partner.id,
            'amount': self.amount_net,
            'currency_id': contract.currency_id.id,
            'date': self.disbursement_date,
            'journal_id': journal.id,
            'payment_method_line_id': payment_method_line.id,
            'ref': f"Disbursement {contract.agreement_no}",
            'contract_id': contract.id,
            'is_finance_disbursement': True,
            'disbursement_principal': self.amount_principal,
            'disbursement_interest': self.amount_interest,
            'disbursement_processing_fee': self.processing_fee,
            'disbursement_processing_fee_tax': self.processing_fee_tax,
            'disbursement_advance_payment': self.advance_payment,
            'disbursement_admin_fee': 0.0,
            'disbursement_commission': contract.commission or 0.0,
        }

        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        contract.disbursement_payment_id = payment.id
        contract.disbursement_move_id = payment.move_id.id
        contract.ac_status = 'active'
        contract.message_post(
            body=_("Disbursement Payment %s created: %s%s (Net Payout %s%s)")
                 % (
                     payment.name,
                     contract.currency_id.symbol,
                     f"{self.amount_principal:,.2f}",
                     contract.currency_id.symbol,
                     f"{self.amount_net:,.2f}"
                 )
        )

        return {
            'name': _('Disbursement Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
        }
