from odoo import models, fields

class FinanceCharge(models.Model):
    _name = 'finance.charge'
    _description = 'Standard Charges and Fees'

    name = fields.Char(string="Charge Name", required=True)
    amount = fields.Float(string="Default Amount")
    type = fields.Selection([
        ('admin', 'Admin Fee'),
        ('other', 'Other Cost'),
        ('penalty', 'Penalty')
    ], required=True)


class FinancePenaltyRule(models.Model):
    _name = 'finance.penalty.rule'
    _description = 'Penalty / Late Interest Configuration'

    name = fields.Char(string="Rule Name", required=True)
    active = fields.Boolean(default=True)
    
    method = fields.Selection([
        ('daily_percent', 'Daily Percentage (Interest)'),
        ('fixed_one_time', 'Fixed One-Time Charge'),
        ('fixed_recurring', 'Fixed Recurring (Monthly)')
    ], string="Calculation Method", default='daily_percent', required=True)
    
    rate = fields.Float(string="Rate (% per Annum)", help="Annual Interest Rate for delay")
    fixed_amount = fields.Monetary(string="Fixed Amount", currency_field='currency_id')
    
    grace_period_days = fields.Integer(string="Grace Period (Days)", default=0, 
                                       help="No penalty if paid within these days")
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)