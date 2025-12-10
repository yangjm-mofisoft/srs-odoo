from odoo import models, fields, api, tools

class FinanceInterestIncomeReport(models.Model):
    _name = 'finance.report.interest'
    _description = 'Interest Income Report'
    _auto = False
    _order = 'agreement_no'

    # --- Contract Details ---
    agreement_no = fields.Char(string="Agreement No", readonly=True)
    hirer_id = fields.Many2one('res.partner', string="Hirer", readonly=True)
    product_id = fields.Many2one('finance.product', string="Product", readonly=True)
    product_type = fields.Selection([
        ('hp', 'Hire Purchase'),
        ('lease', 'Leasing'),
        ('loan', 'General Loan')
    ], string="Type", readonly=True)
    ac_status = fields.Selection([
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('repo', 'Repossessed')
    ], string="Status", readonly=True)

    # --- Financial Details ---
    loan_amount = fields.Monetary(string="Loan Amount", readonly=True, currency_field='currency_id')
    term_charges = fields.Monetary(string="Total Interest", readonly=True, currency_field='currency_id')

    # --- Interest Breakdown ---
    earned_interest = fields.Monetary(string="Earned Interest", readonly=True, currency_field='currency_id')
    unearned_interest = fields.Monetary(string="Unearned Interest", readonly=True, currency_field='currency_id')
    recognized_mtd = fields.Monetary(string="Recognized (MTD)", readonly=True, currency_field='currency_id')

    # --- FIXED: Added Missing Field ---
    progress = fields.Float(string="Progress (%)", readonly=True, group_operator="avg")

    currency_id = fields.Many2one('res.currency', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    fc.id,
                    fc.agreement_no,
                    fc.hirer_id,
                    fc.product_id,
                    fp.product_type,
                    fc.ac_status,
                    fc.currency_id,
                    
                    fc.loan_amount,
                    fc.term_charges,
                    
                    -- Earned Interest
                    COALESCE(fc.interest_derived, 0) as earned_interest,
                    
                    -- Unearned Interest
                    (COALESCE(fc.term_charges, 0) - COALESCE(fc.interest_derived, 0)) as unearned_interest,
                    
                    -- MTD Recognition
                    COALESCE(mtd_payments.interest_portion, 0) as recognized_mtd,

                    -- FIXED: Calculate Progress
                    CASE 
                        WHEN COALESCE(fc.term_charges, 0) != 0 THEN 
                            (COALESCE(fc.interest_derived, 0) / fc.term_charges) * 100
                        ELSE 0
                    END as progress

                FROM finance_contract fc
                LEFT JOIN finance_product fp ON fc.product_id = fp.id
                
                -- Calculate MTD Interest
                LEFT JOIN (
                    SELECT 
                        fcl.contract_id, 
                        SUM(fcl.interest_portion) as interest_portion
                    FROM finance_contract_line fcl
                    WHERE fcl.paid_date >= DATE_TRUNC('month', CURRENT_DATE)
                      AND fcl.paid_date <= CURRENT_DATE
                    GROUP BY fcl.contract_id
                ) mtd_payments ON fc.id = mtd_payments.contract_id

                WHERE fc.ac_status IN ('active', 'closed', 'repo')
            )
        """ % self._table)