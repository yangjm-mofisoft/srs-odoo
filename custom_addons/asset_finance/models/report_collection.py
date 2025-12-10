from odoo import models, fields, api, tools

class FinanceCollectionReport(models.Model):
    _name = 'finance.report.collection'
    _description = 'Collection Report'
    _auto = False
    _order = 'total_overdue_days desc, total_payable desc'

    agreement_no = fields.Char(string="Agreement No", readonly=True)
    hirer_id = fields.Many2one('res.partner', string="Hirer", readonly=True)
    hirer_phone = fields.Char(string="Phone", readonly=True)
    hirer_email = fields.Char(string="Email", readonly=True)

    asset_reg_no = fields.Char(string="Asset", readonly=True)
    product_id = fields.Many2one('finance.product', string="Product", readonly=True)

    # Collection Details
    total_overdue_days = fields.Integer(string="Days Overdue", readonly=True)
    late_status = fields.Selection([
        ('normal', 'Normal'),
        ('attention', 'Attention'),
        ('legal', 'Legal Action')
    ], string="Status", readonly=True)

    # FIXED: balance_installment -> balance_hire
    balance_hire = fields.Monetary(string="Outstanding", readonly=True, currency_field='currency_id')
    balance_late_charges = fields.Monetary(string="Late Charges", readonly=True, currency_field='currency_id')
    balance_misc_fee = fields.Monetary(string="Misc Fees", readonly=True, currency_field='currency_id')
    total_payable = fields.Monetary(string="Total Due", readonly=True, currency_field='currency_id')
    
    priority_score = fields.Integer(string="Priority", readonly=True)
    last_payment_date = fields.Date(string="Last Payment", readonly=True)

    currency_id = fields.Many2one('res.currency', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    fc.id,
                    fc.agreement_no,
                    fc.hirer_id,
                    rp.phone as hirer_phone,
                    rp.email as hirer_email,
                    fc.asset_reg_no,
                    fc.product_id,
                    fc.late_status,
                    fc.currency_id,
                    
                    -- FIXED: fc.balance_installment -> fc.balance_hire
                    fc.balance_hire,
                    COALESCE(fc.balance_late_charges, 0) as balance_late_charges,
                    COALESCE(fc.balance_misc_fee, 0) as balance_misc_fee,
                    
                    -- Calculated Total Payable
                    (COALESCE(fc.balance_hire, 0) + 
                     COALESCE(fc.balance_late_charges, 0) + 
                     COALESCE(fc.balance_misc_fee, 0)) as total_payable,

                    overdue_calc.total_overdue_days,
                    last_pmt.last_payment_date,

                    -- Priority Score (Simple logic: Days * Amount)
                    CASE 
                        WHEN overdue_calc.total_overdue_days > 0 THEN 
                            (overdue_calc.total_overdue_days * (COALESCE(fc.balance_hire, 0) + COALESCE(fc.balance_late_charges, 0) + COALESCE(fc.balance_misc_fee, 0)) / 1000)
                        ELSE 0
                    END as priority_score

                FROM finance_contract fc
                LEFT JOIN res_partner rp ON fc.hirer_id = rp.id
                LEFT JOIN LATERAL (
                    SELECT CASE
                        WHEN MIN(fcl.date_due) IS NOT NULL AND MIN(fcl.date_due) < CURRENT_DATE THEN
                            CURRENT_DATE - MIN(fcl.date_due)
                        ELSE 0
                    END as total_overdue_days
                    FROM finance_contract_line fcl
                    WHERE fcl.contract_id = fc.id
                      AND fcl.date_due < CURRENT_DATE
                      AND fcl.invoice_id IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM account_move am
                          WHERE am.id = fcl.invoice_id
                          AND am.payment_state IN ('paid', 'in_payment')
                      )
                ) overdue_calc ON true
                LEFT JOIN LATERAL (
                    SELECT MAX(ap.date) as last_payment_date
                    FROM account_payment ap
                    WHERE ap.contract_id = fc.id
                      AND ap.state = 'posted'
                      AND ap.payment_type = 'inbound'
                ) last_pmt ON true
                WHERE fc.ac_status = 'active'
                  AND overdue_calc.total_overdue_days > 0
            )
        """ % self._table)