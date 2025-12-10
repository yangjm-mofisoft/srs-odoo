from odoo import models, fields, api, tools

class FinanceDisbursementReport(models.Model):
    _name = 'finance.report.disbursement'
    _description = 'Disbursement Register'
    _auto = False
    _order = 'disbursement_date desc'

    # Contract Details
    agreement_no = fields.Char(string="Agreement No", readonly=True)
    hirer_id = fields.Many2one('res.partner', string="Hirer", readonly=True)
    supplier_id = fields.Many2one('res.partner', string="Supplier", readonly=True)
    asset_reg_no = fields.Char(string="Asset", readonly=True)
    product_id = fields.Many2one('finance.product', string="Product", readonly=True)
    product_type = fields.Selection([
        ('hp', 'Hire Purchase'),
        ('lease', 'Leasing'),
        ('loan', 'General Loan')
    ], string="Type", readonly=True)

    # Disbursement Details
    disbursement_date = fields.Date(string="Disbursement Date", readonly=True)
    disbursement_move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)

    # Financial Breakdown
    cash_price = fields.Monetary(string="Cash Price", readonly=True, currency_field='currency_id')
    down_payment = fields.Monetary(string="Down Payment", readonly=True, currency_field='currency_id')
    loan_amount = fields.Monetary(string="Loan Amount", readonly=True, currency_field='currency_id')
    term_charges = fields.Monetary(string="Interest", readonly=True, currency_field='currency_id')
    balance_hire = fields.Monetary(string="Total Hire", readonly=True, currency_field='currency_id')

    # Terms
    int_rate_pa = fields.Float(string="Interest Rate %", readonly=True)
    no_of_inst = fields.Integer(string="No of Installments", readonly=True)
    monthly_inst = fields.Monetary(string="Monthly Inst", readonly=True, currency_field='currency_id')

    # Fees
    admin_fee = fields.Monetary(string="Admin Fee", readonly=True, currency_field='currency_id')
    commission = fields.Monetary(string="Commission", readonly=True, currency_field='currency_id')

    # Staff
    entry_staff_id = fields.Many2one('res.users', string="Entry Staff", readonly=True)

    currency_id = fields.Many2one('res.currency', readonly=True)

    # Period aggregations
    year = fields.Char(string="Year", readonly=True)
    month = fields.Char(string="Month", readonly=True)
    quarter = fields.Char(string="Quarter", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    fc.id,
                    fc.agreement_no,
                    fc.hirer_id,
                    fc.supplier_id,
                    fc.asset_reg_no,
                    fc.product_id,
                    fp.product_type,
                    am.date as disbursement_date,
                    fc.disbursement_move_id,
                    fc.cash_price,
                    fc.down_payment,
                    fc.loan_amount,
                    fc.term_charges,
                    fc.balance_hire,
                    fc.int_rate_pa,
                    ft.months as no_of_inst,
                    fc.monthly_inst,
                    fc.admin_fee,
                    fc.commission,
                    fc.entry_staff_id,
                    fc.currency_id,
                    TO_CHAR(am.date, 'YYYY') as year,
                    TO_CHAR(am.date, 'YYYY-MM') as month,
                    'Q' || TO_CHAR(am.date, 'Q') || ' ' || TO_CHAR(am.date, 'YYYY') as quarter
                FROM finance_contract fc
                LEFT JOIN account_move am ON fc.disbursement_move_id = am.id
                LEFT JOIN finance_product fp ON fc.product_id = fp.id
                LEFT JOIN finance_term ft ON fc.no_of_inst = ft.id
                WHERE fc.disbursement_move_id IS NOT NULL
                  AND am.state = 'posted'
            )
        """ % self._table)
