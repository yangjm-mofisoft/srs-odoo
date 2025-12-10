from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # --------------------------------------------------------
    # ASSET FINANCE CONFIGURATION PARAMETERS
    # --------------------------------------------------------

    # HP Act Limit
    hp_act_limit = fields.Monetary(
        string="HP Act Limit",
        default=55000.0,
        currency_field='currency_id',
        config_parameter='asset_finance.hp_act_limit',
        help="Hire Purchase Act applies to contracts with loan amounts at or below this limit."
    )

    # Grace Period
    grace_period_days = fields.Integer(
        string="Payment Grace Period (Days)",
        default=7,
        config_parameter='asset_finance.grace_period_days',
        help="Number of days after due date before penalties start accruing."
    )

    # Settlement Rebate Fee
    settlement_rebate_fee = fields.Float(
        string="Settlement Rebate Fee (%)",
        default=20.0,
        config_parameter='asset_finance.settlement_rebate_fee',
        help="Percentage of unearned interest charged as rebate fee for early settlement."
    )

    # Late Status Thresholds
    late_attention_days = fields.Integer(
        string="Late Status: Attention (Days)",
        default=30,
        config_parameter='asset_finance.late_attention_days',
        help="Number of overdue days before contract status changes to 'Attention'."
    )

    late_legal_days = fields.Integer(
        string="Late Status: Legal Action (Days)",
        default=90,
        config_parameter='asset_finance.late_legal_days',
        help="Number of overdue days before contract status changes to 'Legal Action'."
    )

    # Accounting Configuration
    admin_fee_account_id = fields.Many2one(
        'account.account',
        string="Admin Fee Expense Account",
        config_parameter='asset_finance.admin_fee_account_id',
        help="Account used for admin fee expenses during disbursement."
    )

    penalty_income_account_id = fields.Many2one(
        'account.account',
        string="Penalty Income Account",
        config_parameter='asset_finance.penalty_income_account_id',
        help="Account used to record penalty/late charge income."
    )

    # Interest Recognition
    auto_recognize_interest = fields.Boolean(
        string="Auto Recognize Interest Monthly",
        default=True,
        config_parameter='asset_finance.auto_recognize_interest',
        help="Automatically recognize earned interest monthly via scheduled action."
    )

    # Collection Settings
    auto_send_reminders = fields.Boolean(
        string="Auto Send Payment Reminders",
        default=False,
        config_parameter='asset_finance.auto_send_reminders',
        help="Automatically send payment reminders X days before due date."
    )

    reminder_days_before = fields.Integer(
        string="Send Reminder (Days Before)",
        default=3,
        config_parameter='asset_finance.reminder_days_before',
        help="Number of days before installment due date to send reminder."
    )

    # Currency
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True
    )

    @api.model
    def get_values(self):
        """Override to load configuration values"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        # Handle Many2one fields separately
        admin_fee_account = params.get_param('asset_finance.admin_fee_account_id', default=False)
        penalty_income_account = params.get_param('asset_finance.penalty_income_account_id', default=False)

        res.update(
            admin_fee_account_id=int(admin_fee_account) if admin_fee_account else False,
            penalty_income_account_id=int(penalty_income_account) if penalty_income_account else False,
        )

        return res

    def set_values(self):
        """Override to save configuration values"""
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()

        # Handle Many2one fields separately
        params.set_param('asset_finance.admin_fee_account_id', self.admin_fee_account_id.id or False)
        params.set_param('asset_finance.penalty_income_account_id', self.penalty_income_account_id.id or False)
