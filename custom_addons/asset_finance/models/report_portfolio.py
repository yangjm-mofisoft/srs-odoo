from odoo import models, fields, api, tools

class FinancePortfolioReport(models.Model):
    _name = 'finance.report.portfolio'
    _description = 'Portfolio Summary Report'
    _auto = False
    _order = 'product_type, asset_type, ac_status'

    # Grouping Dimensions
    product_id = fields.Many2one('finance.product', string="Product", readonly=True)
    product_type = fields.Selection([
        ('hp', 'Hire Purchase'),
        ('lease', 'Leasing'),
        ('loan', 'General Loan')
    ], string="Product Type", readonly=True)

    asset_type = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('machinery', 'Machinery'),
        ('equipment', 'Equipment'),
        ('property', 'Property'),
        ('other', 'Other')
    ], string="Asset Type", readonly=True)

    ac_status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('repo', 'Repossessed')
    ], string="Status", readonly=True)

    # Count Metrics
    contract_count = fields.Integer(string="Number of Contracts", readonly=True)

    # Financial Metrics
    total_cash_price = fields.Monetary(string="Total Cash Price", readonly=True, currency_field='currency_id')
    total_down_payment = fields.Monetary(string="Total Down Payment", readonly=True, currency_field='currency_id')
    total_loan_amount = fields.Monetary(string="Total Loan Amount", readonly=True, currency_field='currency_id')
    total_interest = fields.Monetary(string="Total Interest", readonly=True, currency_field='currency_id')
    total_hire = fields.Monetary(string="Total Hire", readonly=True, currency_field='currency_id')

    # Outstanding Metrics
    total_outstanding = fields.Monetary(string="Total Outstanding", readonly=True, currency_field='currency_id')
    total_overdue = fields.Monetary(string="Total Overdue", readonly=True, currency_field='currency_id')
    total_penalties = fields.Monetary(string="Total Penalties", readonly=True, currency_field='currency_id')

    # Averages
    avg_loan_amount = fields.Monetary(string="Avg Loan Amount", readonly=True, currency_field='currency_id')
    avg_interest_rate = fields.Float(string="Avg Interest Rate %", readonly=True)
    avg_term_months = fields.Float(string="Avg Term (Months)", readonly=True)

    # Risk Metrics
    overdue_percentage = fields.Float(string="Overdue %", readonly=True)
    avg_days_overdue = fields.Float(string="Avg Days Overdue", readonly=True)

    # Performance Metrics (Active contracts only)
    collection_rate = fields.Float(string="Collection Rate %", readonly=True)

    currency_id = fields.Many2one('res.currency', readonly=True)

    # Period
    year = fields.Char(string="Year", readonly=True)
    month = fields.Char(string="Month", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY fp.product_type, fc.asset_type, fc.ac_status) as id,

                    -- Grouping dimensions
                    fc.product_id,
                    fp.product_type,
                    fc.asset_type,
                    fc.ac_status,

                    -- Count
                    COUNT(fc.id) as contract_count,

                    -- Financial totals
                    SUM(fc.cash_price) as total_cash_price,
                    SUM(fc.down_payment) as total_down_payment,
                    SUM(fc.loan_amount) as total_loan_amount,
                    SUM(fc.term_charges) as total_interest,
                    SUM(fc.balance_hire) as total_hire,

                    -- Outstanding metrics (calculated from stored fields)
                    SUM(fc.balance_hire - COALESCE(fc.total_inst_paid, 0)) as total_outstanding,
                    SUM(CASE
                        WHEN overdue_info.is_overdue THEN fc.balance_hire - COALESCE(fc.total_inst_paid, 0)
                        ELSE 0
                    END) as total_overdue,
                    SUM(fc.accrued_penalty) as total_penalties,

                    -- Averages
                    AVG(fc.loan_amount) as avg_loan_amount,
                    AVG(fc.int_rate_pa) as avg_interest_rate,
                    AVG(ft.months) as avg_term_months,

                    -- Risk metrics
                    CASE
                        WHEN SUM(fc.balance_hire - COALESCE(fc.total_inst_paid, 0)) > 0 THEN
                            (SUM(CASE
                                WHEN overdue_info.is_overdue THEN fc.balance_hire - COALESCE(fc.total_inst_paid, 0)
                                ELSE 0
                            END) / SUM(fc.balance_hire - COALESCE(fc.total_inst_paid, 0))) * 100
                        ELSE 0
                    END as overdue_percentage,

                    AVG(COALESCE(overdue_info.days_overdue, 0)) as avg_days_overdue,

                    -- Collection rate: (Total Paid / Total Expected) * 100
                    CASE
                        WHEN SUM(fc.balance_hire) > 0 THEN
                            (SUM(COALESCE(fc.total_inst_paid, 0)) / SUM(fc.balance_hire)) * 100
                        ELSE 0
                    END as collection_rate,

                    -- Currency
                    fc.currency_id,

                    -- Period
                    TO_CHAR(CURRENT_DATE, 'YYYY') as year,
                    TO_CHAR(CURRENT_DATE, 'YYYY-MM') as month

                FROM finance_contract fc
                LEFT JOIN finance_product fp ON fc.product_id = fp.id
                LEFT JOIN finance_term ft ON fc.no_of_inst = ft.id
                LEFT JOIN LATERAL (
                    SELECT
                        CASE
                            WHEN MIN(fcl.date_due) IS NOT NULL AND MIN(fcl.date_due) < CURRENT_DATE THEN TRUE
                            ELSE FALSE
                        END as is_overdue,
                        CASE
                            WHEN MIN(fcl.date_due) IS NOT NULL AND MIN(fcl.date_due) < CURRENT_DATE THEN
                                CURRENT_DATE - MIN(fcl.date_due)
                            ELSE 0
                        END as days_overdue
                    FROM finance_contract_line fcl
                    WHERE fcl.contract_id = fc.id
                      AND fcl.date_due < CURRENT_DATE
                      AND fcl.invoice_id IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM account_move am
                          WHERE am.id = fcl.invoice_id
                          AND am.payment_state IN ('paid', 'in_payment')
                      )
                ) overdue_info ON true

                GROUP BY
                    fc.product_id,
                    fp.product_type,
                    fc.asset_type,
                    fc.ac_status,
                    fc.currency_id

                HAVING COUNT(fc.id) > 0
            )
        """ % self._table)
