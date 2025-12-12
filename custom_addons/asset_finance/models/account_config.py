from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FinanceAccountConfig(models.Model):
    _name = 'finance.account.config'
    _description = 'Finance Account Configuration'
    _rec_name = 'company_id'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, index=True)

    # === ASSET ACCOUNTS ===
    hp_debtors_account_id = fields.Many2one('account.account', string='HP Debtors (Principal + Interest)',
                                            domain="[('account_type', '=', 'asset_receivable')]",
                                            required=True,
                                            help="Account for Hire Purchase Debtors - tracks principal and interest receivable (e.g., 2002)")

    unearned_interest_account_id = fields.Many2one('account.account', string='Unearned Interest',
                                                   domain="[('account_type', 'in', ['asset_current', 'liability_current'])]",
                                                   required=True,
                                                   help="Contra-asset or liability account for unearned interest (e.g., 2003)")

    hp_charges_account_id = fields.Many2one('account.account', string='HP Debtors - Other Charges',
                                            domain="[('account_type', 'in', ['asset_receivable', 'asset_current'])]",
                                            required=True,
                                            help="Account for processing fees and other charges receivable (e.g., 2004)")

    installment_contra_account_id = fields.Many2one('account.account', string='Installment Contra Account',
                                                    domain="[('account_type', '=', 'asset_current')]",
                                                    help="Account for installment contra entries (e.g., 2005)")

    # === INCOME ACCOUNTS ===
    interest_income_account_id = fields.Many2one('account.account', string='Interest Income',
                                                 domain="[('account_type', '=', 'income')]",
                                                 required=True,
                                                 help="Revenue account for interest income (e.g., 5001)")

    processing_fee_income_account_id = fields.Many2one('account.account', string='Processing Fee Income',
                                                       domain="[('account_type', '=', 'income')]",
                                                       required=True,
                                                       help="Revenue account for processing fees (e.g., 5002)")

    late_charges_income_account_id = fields.Many2one('account.account', string='Late Charges Income',
                                                     domain="[('account_type', '=', 'income')]",
                                                     required=True,
                                                     help="Revenue account for late charges and penalties (e.g., 5003)")

    early_settlement_income_account_id = fields.Many2one('account.account', string='Early Settlement Fee Income',
                                                         domain="[('account_type', '=', 'income')]",
                                                         help="Revenue account for early settlement fees (e.g., 5004)")

    # === TAX ACCOUNT ===
    gst_output_account_id = fields.Many2one('account.account', string='GST Output Tax',
                                            domain="[('account_type', '=', 'liability_current')]",
                                            required=True,
                                            help="Liability account for GST/tax payable (e.g., 6004)")

    # === EXPENSE ACCOUNTS (Optional - for Block Discounting) ===
    block_interest_expense_account_id = fields.Many2one('account.account', string='Block Discounting Interest Expense',
                                                        domain="[('account_type', '=', 'expense_direct_cost')]",
                                                        help="Cost account for block discounting interest (e.g., 6001)")

    repo_expense_account_id = fields.Many2one('account.account', string='Repossession Expenses',
                                              domain="[('account_type', '=', 'expense_direct_cost')]",
                                              help="Cost account for repossession expenses (e.g., 6003)")

    bank_charges_account_id = fields.Many2one('account.account', string='Bank Charges',
                                              domain="[('account_type', '=', 'expense')]",
                                              help="Expense account for bank charges (e.g., 8001)")

    _sql_constraints = [
        ('company_uniq', 'unique(company_id)', 'Only one account configuration per company is allowed!')
    ]

    @api.model
    def get_config(self, company_id=None):
        """Get account configuration for the current or specified company"""
        if not company_id:
            company_id = self.env.company.id

        config = self.search([('company_id', '=', company_id)], limit=1)
        if not config:
            raise UserError(_(
                "Finance Account Configuration not found for company '%s'. "
                "Please configure it in Finance > Configuration > Account Mapping."
            ) % self.env.company.name)
        return config

    @api.model
    def get_account(self, account_type, company_id=None):
        """
        Get a specific account by type from configuration

        Args:
            account_type (str): One of: 'hp_debtors', 'unearned_interest', 'hp_charges',
                               'interest_income', 'processing_fee_income', 'late_charges_income',
                               'gst_output', etc.
            company_id (int): Optional company ID

        Returns:
            account.account: The configured account
        """
        config = self.get_config(company_id)
        field_name = f"{account_type}_account_id"

        if not hasattr(config, field_name):
            raise UserError(_("Invalid account type: %s") % account_type)

        account = getattr(config, field_name)
        if not account:
            raise UserError(_(
                "Account type '%s' is not configured. "
                "Please configure it in Finance > Configuration > Account Mapping."
            ) % account_type.replace('_', ' ').title())

        return account

    def action_auto_configure_from_coa(self):
        """
        Auto-configure accounts by searching for accounts with standard codes
        This is a helper action for initial setup
        """
        self.ensure_one()
        Account = self.env['account.account']

        # Mapping of field names to account codes (based on standard COA)
        code_mapping = {
            'hp_debtors_account_id': '2002',
            'unearned_interest_account_id': '2003',
            'hp_charges_account_id': '2004',
            'installment_contra_account_id': '2005',
            'interest_income_account_id': '5001',
            'processing_fee_income_account_id': '5002',
            'late_charges_income_account_id': '5003',
            'early_settlement_income_account_id': '5004',
            'gst_output_account_id': '6004',
            'block_interest_expense_account_id': '6001',
            'repo_expense_account_id': '6003',
            'bank_charges_account_id': '8001',
        }

        updates = {}
        for field_name, code in code_mapping.items():
            # Search for account by code only (no company_id filter as it's not searchable in Odoo 19)
            account = Account.search([('code', '=', code)], limit=1)

            if account:
                updates[field_name] = account.id

        if updates:
            self.write(updates)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Found and configured %d accounts automatically.') % len(updates),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _('No accounts found with standard codes. Please configure manually.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
