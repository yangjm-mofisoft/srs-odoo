from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # --------------------------------------------------------
    # ASSET FINANCE CONFIGURATION PARAMETERS
    # --------------------------------------------------------

    # Supported Asset Types - Individual Checkboxes
    support_asset_type_vehicle = fields.Boolean(
        string="Vehicle",
        default=True,
        help="Enable Vehicle as a supported asset type"
    )

    support_asset_type_equipment = fields.Boolean(
        string="Equipment",
        default=False,
        help="Enable Equipment as a supported asset type"
    )

    support_asset_type_property = fields.Boolean(
        string="Property",
        default=False,
        help="Enable Property as a supported asset type"
    )

    support_asset_type_other = fields.Boolean(
        string="Other",
        default=False,
        help="Enable Other as a supported asset type"
    )

    # Default Asset Type (Selection field, dynamically populated from supported types)
    # Note: Cannot use 'default_' prefix as it conflicts with Odoo's default_get mechanism
    asset_type_default = fields.Selection(
        selection='_get_asset_type_default_selection',
        string="Default Asset Type",
        help="The default asset type pre-selected when creating a new asset"
    )

    @api.model
    def _get_asset_type_default_selection(self):
        """Dynamically generate default asset type selection based on supported types"""
        # Build supported types from current checkbox values in the form
        # This ensures the dropdown updates in real-time when checkboxes change
        supported = []

        # Try to get current form values first (for real-time updates)
        if hasattr(self, 'support_asset_type_vehicle') and self.support_asset_type_vehicle:
            supported.append('vehicle')
        if hasattr(self, 'support_asset_type_equipment') and self.support_asset_type_equipment:
            supported.append('equipment')
        if hasattr(self, 'support_asset_type_property') and self.support_asset_type_property:
            supported.append('property')
        if hasattr(self, 'support_asset_type_other') and self.support_asset_type_other:
            supported.append('other')

        # If no checkboxes are checked (initial load), get from saved config
        if not supported:
            param = self.env['ir.config_parameter'].sudo().search([
                ('key', '=', 'asset_finance.supported_asset_types')
            ], limit=1)
            supported_str = param.value if param and param.value else 'vehicle'
            supported = [s.strip() for s in supported_str.split(',')]

        # All available types
        all_types = {
            'vehicle': 'Vehicle',
            'equipment': 'Equipment',
            'property': 'Property',
            'other': 'Other'
        }

        # Return only supported types
        result = [(key, all_types[key]) for key in supported if key in all_types]
        return result if result else [('vehicle', 'Vehicle')]

    @api.onchange('support_asset_type_vehicle', 'support_asset_type_equipment',
                  'support_asset_type_property', 'support_asset_type_other')
    def _onchange_supported_asset_types(self):
        """Clear default asset type if it's no longer in supported types"""
        if not self.asset_type_default:
            return

        # Build current supported types list
        supported = []
        if self.support_asset_type_vehicle:
            supported.append('vehicle')
        if self.support_asset_type_equipment:
            supported.append('equipment')
        if self.support_asset_type_property:
            supported.append('property')
        if self.support_asset_type_other:
            supported.append('other')

        # If current default is not in supported list, clear it
        if self.asset_type_default not in supported:
            self.asset_type_default = False

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
        config_parameter='asset_finance.settlement_rebate_fee_pct',
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

    disbursement_journal_id = fields.Many2one(
        'account.journal',
        string="Disbursement Journal",
        domain="[('type', 'in', ['bank', 'cash'])]",
        help="Default bank journal used when posting disbursement payments."
    )

    interest_recognition_journal_id = fields.Many2one(
        'account.journal',
        string="Interest Recognition Journal",
        domain="[('type', '=', 'general')]",
        help="Journal used by the monthly interest recognition cron job."
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
        """Override to load configuration values for Many2one fields and asset type checkboxes"""
        res = super(ResConfigSettings, self).get_values()

        IrConfigParam = self.env['ir.config_parameter'].sudo()

        # Get Many2one field values from config parameters
        admin_fee_param = IrConfigParam.search([
            ('key', '=', 'asset_finance.admin_fee_account_id')
        ], limit=1)
        penalty_income_param = IrConfigParam.search([
            ('key', '=', 'asset_finance.penalty_income_account_id')
        ], limit=1)
        disbursement_journal_param = IrConfigParam.search([
            ('key', '=', 'asset_finance.disbursement_journal_id')
        ], limit=1)
        interest_journal_param = IrConfigParam.search([
            ('key', '=', 'asset_finance.interest_recognition_journal_id')
        ], limit=1)

        admin_fee_account = admin_fee_param.value if admin_fee_param else ''
        penalty_income_account = penalty_income_param.value if penalty_income_param else ''
        disbursement_journal = disbursement_journal_param.value if disbursement_journal_param else ''
        interest_journal = interest_journal_param.value if interest_journal_param else ''

        # Get supported asset types from config parameter
        supported_types_param = IrConfigParam.search([
            ('key', '=', 'asset_finance.supported_asset_types')
        ], limit=1)
        supported_str = supported_types_param.value if supported_types_param else 'vehicle'
        supported_list = [s.strip() for s in supported_str.split(',')]

        # Get default asset type from config parameter
        default_type_param = IrConfigParam.search([
            ('key', '=', 'asset_finance.default_asset_type')
        ], limit=1)
        default_type = default_type_param.value if default_type_param else 'vehicle'

        res.update(
            admin_fee_account_id=int(admin_fee_account) if admin_fee_account and admin_fee_account != 'False' else False,
            penalty_income_account_id=int(penalty_income_account) if penalty_income_account and penalty_income_account != 'False' else False,
            disbursement_journal_id=int(disbursement_journal) if disbursement_journal and disbursement_journal != 'False' else False,
            interest_recognition_journal_id=int(interest_journal) if interest_journal and interest_journal != 'False' else False,
            support_asset_type_vehicle='vehicle' in supported_list,
            support_asset_type_equipment='equipment' in supported_list,
            support_asset_type_property='property' in supported_list,
            support_asset_type_other='other' in supported_list,
            asset_type_default=default_type,
        )

        return res

    def set_values(self):
        """Override to save configuration values for Many2one fields and asset type checkboxes"""
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

        # Disbursement journal
        param_disbursement = IrConfigParam.search([('key', '=', 'asset_finance.disbursement_journal_id')], limit=1)
        value_disbursement = str(self.disbursement_journal_id.id) if self.disbursement_journal_id else 'False'
        if param_disbursement:
            param_disbursement.write({'value': value_disbursement})
        else:
            IrConfigParam.create({'key': 'asset_finance.disbursement_journal_id', 'value': value_disbursement})

        # Interest recognition journal
        param_interest = IrConfigParam.search([('key', '=', 'asset_finance.interest_recognition_journal_id')], limit=1)
        value_interest = str(self.interest_recognition_journal_id.id) if self.interest_recognition_journal_id else 'False'
        if param_interest:
            param_interest.write({'value': value_interest})
        else:
            IrConfigParam.create({'key': 'asset_finance.interest_recognition_journal_id', 'value': value_interest})

        # Build supported asset types from checkboxes
        supported_types = []
        if self.support_asset_type_vehicle:
            supported_types.append('vehicle')
        if self.support_asset_type_equipment:
            supported_types.append('equipment')
        if self.support_asset_type_property:
            supported_types.append('property')
        if self.support_asset_type_other:
            supported_types.append('other')

        # Validate: At least one asset type must be supported
        if not supported_types:
            raise ValidationError(_('At least one asset type must be supported.'))

        # Validate: Default asset type must be set
        if not self.asset_type_default:
            raise ValidationError(_('Default Asset Type cannot be empty. Please select a default asset type.'))

        # Validate: Default asset type must be one of the supported types
        if self.asset_type_default not in supported_types:
            raise ValidationError(
                _('Default Asset Type "%s" is not in the list of supported asset types. '
                  'Please select a supported asset type or enable it first.') % self.asset_type_default
            )

        # Save supported types as comma-separated string
        supported_str = ','.join(supported_types)
        param_supported = IrConfigParam.search([('key', '=', 'asset_finance.supported_asset_types')], limit=1)
        if param_supported:
            param_supported.write({'value': supported_str})
        else:
            IrConfigParam.create({'key': 'asset_finance.supported_asset_types', 'value': supported_str})

        # Save default asset type
        param_default = IrConfigParam.search([('key', '=', 'asset_finance.default_asset_type')], limit=1)
        if param_default:
            param_default.write({'value': self.asset_type_default})
        else:
            IrConfigParam.create({'key': 'asset_finance.default_asset_type', 'value': self.asset_type_default})
