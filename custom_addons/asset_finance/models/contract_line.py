from odoo import models, fields

class FinanceContractLine(models.Model):
    _name = 'finance.contract.line'
    _description = 'Amortization Schedule Line'
    _order = 'sequence, date_due'

    contract_id = fields.Many2one('finance.contract', string="Contract", ondelete='cascade')
    sequence = fields.Integer(string="#")
    date_due = fields.Date(string="Due Date")

    amount_principal = fields.Monetary(string="Principal")
    amount_interest = fields.Monetary(string="Interest")
    amount_total = fields.Monetary(string="Total Installment")
    interest_portion = fields.Monetary(string="Interest Portion", related='amount_interest', store=True)

    # Link to Accounting (The "Movements" you asked about earlier)
    invoice_id = fields.Many2one('account.move', string="Invoice")
    state = fields.Selection(related='invoice_id.state', string="Status")

    # Payment tracking
    paid_date = fields.Date(string="Paid Date")

    # Penalty tracking
    penalty_last_applied_date = fields.Date(string="Last Penalty Date", readonly=True,
        help="The date the last penalty was calculated for this overdue line. "
             "Used to ensure daily penalties are not applied more than once a day.")

    # Interest recognition tracking
    interest_recognized = fields.Boolean(string="Interest Recognized", default=False,
        help="Used to track if interest has been recognized in accounting")

    currency_id = fields.Many2one(related='contract_id.currency_id')