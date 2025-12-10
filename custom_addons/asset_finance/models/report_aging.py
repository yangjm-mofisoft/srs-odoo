from odoo import models, fields, api, tools

class FinanceAgingReport(models.Model):
    _name = 'finance.report.aging'
    _description = 'Aging Analysis Report'
    _auto = False
    _order = 'total_overdue_days desc, balance_hire desc'

    agreement_no = fields.Char(string="Agreement No", readonly=True)
    hirer_id = fields.Many2one('res.partner', string="Hirer", readonly=True)
    asset_reg_no = fields.Char(string="Asset Reg", readonly=True)
    asset_make = fields.Char(string="Make", readonly=True)
    asset_model = fields.Char(string="Model", readonly=True)
    product_id = fields.Many2one('finance.product', string="Product", readonly=True)

    # FIXED: Field Name
    balance_hire = fields.Monetary(string="Outstanding Balance", readonly=True, currency_field='currency_id')
    
    accrued_penalty = fields.Monetary(string="Penalties", readonly=True, currency_field='currency_id')
    balance_late_charges = fields.Monetary(string="Late Charges", readonly=True, currency_field='currency_id')
    total_payable = fields.Monetary(string="Total Payable", readonly=True, currency_field='currency_id')

    total_overdue_days = fields.Integer(string="Days Overdue", readonly=True)
    late_status = fields.Selection([('normal','Normal'),('attention','Attention'),('legal','Legal Action')], string="Late Status", readonly=True)
    ac_status = fields.Selection([('draft','Draft'),('active','Active'),('closed','Closed'),('repo','Repossessed')], string="Status", readonly=True)
    aging_bucket = fields.Selection([('current','Current'),('1_30','1-30 Days'),('31_60','31-60 Days'),('61_90','61-90 Days'),('90_plus','90+ Days')], string="Aging Bucket", readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    fc.id,
                    fc.agreement_no,
                    fc.hirer_id,
                    fc.asset_reg_no,
                    fc.asset_make,
                    fc.asset_model,
                    fc.product_id,
                    fc.ac_status,
                    fc.currency_id,
                    
                    -- FIXED: Use balance_hire column
                    fc.balance_hire,
                    COALESCE(fc.accrued_penalty, 0) as accrued_penalty,
                    0 as balance_late_charges,
                    (COALESCE(fc.balance_hire, 0) + COALESCE(fc.accrued_penalty, 0)) as total_payable,

                    fc.late_status,

                    CASE 
                        WHEN MIN(fcl.date_due) IS NOT NULL AND MIN(fcl.date_due) < CURRENT_DATE THEN 
                            CURRENT_DATE - MIN(fcl.date_due)
                        ELSE 0
                    END as total_overdue_days,

                    CASE
                        WHEN MIN(fcl.date_due) IS NULL OR MIN(fcl.date_due) >= CURRENT_DATE THEN 'current'
                        WHEN CURRENT_DATE - MIN(fcl.date_due) BETWEEN 1 AND 30 THEN '1_30'
                        WHEN CURRENT_DATE - MIN(fcl.date_due) BETWEEN 31 AND 60 THEN '31_60'
                        WHEN CURRENT_DATE - MIN(fcl.date_due) BETWEEN 61 AND 90 THEN '61_90'
                        ELSE '90_plus'
                    END as aging_bucket

                FROM finance_contract fc
                LEFT JOIN finance_contract_line fcl ON fc.id = fcl.contract_id
                    AND fcl.date_due < CURRENT_DATE
                    AND fcl.invoice_id IS NOT NULL
                    AND NOT EXISTS (SELECT 1 FROM account_move am WHERE am.id = fcl.invoice_id AND am.payment_state IN ('paid', 'in_payment'))
                
                WHERE fc.ac_status IN ('active', 'repo')
                
                GROUP BY 
                    fc.id, fc.agreement_no, fc.hirer_id, fc.asset_reg_no, fc.asset_make,
                    fc.asset_model, fc.product_id, fc.balance_hire, fc.ac_status,
                    fc.late_status, fc.accrued_penalty, fc.currency_id
            )
        """ % self._table)