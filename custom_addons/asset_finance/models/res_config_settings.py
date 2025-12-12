from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # --------------------------------------------------------
    # ASSET FINANCE CONFIGURATION PARAMETERS
    # --------------------------------------------------------

    # HP Act Limit
    hp_act_limit = fields.Float(
        string="HP Act Limit",
        default=55000.0,
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
        help="Account used for admin fee expenses during disbursement."
    )

    penalty_income_account_id = fields.Many2one(
        'account.account',
        string="Penalty Income Account",
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
        """Override to load configuration values for Many2one fields"""
        res = super(ResConfigSettings, self).get_values()

        # Get Many2one field values from config parameters
        # Note: We search for the parameter records directly
        admin_fee_param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'asset_finance.admin_fee_account_id')
        ], limit=1)
        penalty_income_param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'asset_finance.penalty_income_account_id')
        ], limit=1)

        admin_fee_account = admin_fee_param.value if admin_fee_param else ''
        penalty_income_account = penalty_income_param.value if penalty_income_param else ''

        res.update(
            admin_fee_account_id=int(admin_fee_account) if admin_fee_account and admin_fee_account != 'False' else False,
            penalty_income_account_id=int(penalty_income_account) if penalty_income_account and penalty_income_account != 'False' else False,
        )

        return res

    def set_values(self):
        """Override to save configuration values for Many2one fields"""
        super(ResConfigSettings, self).set_values()

        # Save Many2one field values to config parameters
        # In Odoo 19, use create/write directly instead of set_param
        IrConfigParam = self.env['ir.config_parameter'].sudo()

        # Admin fee account
        param_admin = IrConfigParam.search([('key', '=', 'asset_finance.admin_fee_account_id')], limit=1)
        value_admin = str(self.admin_fee_account_id.id) if self.admin_fee_account_id else 'False'
        if param_admin:
            param_admin.write({'value': value_admin})
        else:
            IrConfigParam.create({'key': 'asset_finance.admin_fee_account_id', 'value': value_admin})

        # Penalty income account
        param_penalty = IrConfigParam.search([('key', '=', 'asset_finance.penalty_income_account_id')], limit=1)
        value_penalty = str(self.penalty_income_account_id.id) if self.penalty_income_account_id else 'False'
        if param_penalty:
            param_penalty.write({'value': value_penalty})
        else:
            IrConfigParam.create({'key': 'asset_finance.penalty_income_account_id', 'value': value_penalty})
