from odoo import models, fields

class LeasingContractLine(models.Model):
    _name = 'leasing.contract.line'
    _description = 'Amortization Schedule Line'
    _order = 'sequence, date_due'

    contract_id = fields.Many2one('leasing.contract', string="Contract", ondelete='cascade')
    sequence = fields.Integer(string="#")
    date_due = fields.Date(string="Due Date")
    
    amount_principal = fields.Monetary(string="Principal")
    amount_interest = fields.Monetary(string="Interest")
    amount_total = fields.Monetary(string="Total Installment")
    
    # Link to Accounting (The "Movements" you asked about earlier)
    invoice_id = fields.Many2one('account.move', string="Invoice")
    state = fields.Selection(related='invoice_id.state', string="Status")
    
    currency_id = fields.Many2one(related='contract_id.currency_id')