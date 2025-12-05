from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FinanceProduct(models.Model):
    _name = 'finance.product'
    _description = 'Financial Product'
    _check_company_auto = True

    name = fields.Char(string="Product Name", required=True)
    active = fields.Boolean(default=True)
    
    # SIMPLIFICATION: Type defined directly here instead of a separate group table
    product_type = fields.Selection([
        ('hp', 'Hire Purchase'),
        ('lease', 'Leasing'),
        ('loan', 'General Loan')
    ], string="Product Type", required=True, default='hp')
    
    # Validity Range
    date_start = fields.Date(string="Valid From")
    date_end = fields.Date(string="Valid Until")
    
    # Default Terms
    default_int_rate = fields.Float(string="Default Interest Rate (%)")
    min_finance_amount = fields.Monetary(string="Min Finance Amount", currency_field='currency_id')
    max_finance_amount = fields.Monetary(string="Max Finance Amount", currency_field='currency_id')
    
    # NEW: Finance Percentage Limits
    min_finance_percent = fields.Float(string="Min Finance Percentage (%)", help="Minimum Loan to Value Ratio")
    max_finance_percent = fields.Float(string="Max Finance Percentage (%)", help="Maximum Loan to Value Ratio")
    
    # Leasing Specific Defaults (Only used if product_type == 'lease')
    default_rv_percentage = fields.Float(string="Default Residual Value (%)")
    annual_mileage_limit = fields.Integer(string="Annual Mileage Limit (km)")
    excess_mileage_charge = fields.Monetary(string="Excess Mileage Charge (per km)")
    
    # Penalty setting
    default_penalty_rule_id = fields.Many2one('finance.penalty.rule', string="Default Penalty Rule")

    # Term settings
    min_months = fields.Integer(string="Min. Term (Months)", default=12)
    max_months = fields.Integer(string="Max. Term (Months)", default=60)
    step_months = fields.Integer(string="Term Step (Months)", default=12, help="e.g., a step of 12 means terms can be 12, 24, 36...")

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_start > rec.date_end:
                raise ValidationError("Start Date cannot be after End Date")