from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class FinanceContractGuarantor(models.Model):
    _name = 'finance.contract.guarantor'
    _description = 'Guarantor Line'

    contract_id = fields.Many2one('finance.contract', string="Contract", ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Guarantor Name", required=True,
                                 domain="[('finance_partner_type', 'in', [False, '']), ('finance_blacklist', '=', False)]",
                                 help="Select an individual or company to act as guarantor (not a broker/insurer/finance company/supplier).")

    # --- 1. Pull Details from res.partner ---
    nric = fields.Char(related='partner_id.nric', string="NRIC / ID No", readonly=True)
    email = fields.Char(related='partner_id.email', readonly=True)
    phone = fields.Char(related='partner_id.phone', readonly=True)

    # Address Block
    street = fields.Char(related='partner_id.street', readonly=True)
    street2 = fields.Char(related='partner_id.street2', readonly=True)
    city = fields.Char(related='partner_id.city', readonly=True)
    zip = fields.Char(related='partner_id.zip', readonly=True)

    # --- 2. Compliance / Deal Specific Fields ---
    relationship = fields.Selection([
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('business_partner', 'Business Partner'),
        ('director', 'Director'),
        ('other', 'Other')
    ], string="Relationship", required=True)

    income_verified = fields.Boolean(string="Income Verified")
    verification_date = fields.Date(string="Verified Date", default=fields.Date.context_today)
    remarks = fields.Char(string="Remarks")


class FinanceContractJointHirer(models.Model):
    _name = 'finance.contract.joint.hirer'
    _description = 'Co-Borrower Line'

    contract_id = fields.Many2one('finance.contract', string="Contract", ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Co-Borrower Name", required=True,
                                 domain="[('finance_partner_type', 'in', [False, '']), ('finance_blacklist', '=', False)]",
                                 help="Select an individual or company to act as co-borrower (not a broker/insurer/finance company/supplier).")

    # --- Pull Details from res.partner ---
    nric = fields.Char(related='partner_id.nric', string="NRIC / ID No", readonly=True)
    email = fields.Char(related='partner_id.email', readonly=True)
    phone = fields.Char(related='partner_id.phone', readonly=True)

    # --- Compliance Fields ---
    share_percentage = fields.Float(string="Liability Share (%)", default=100.0)
    relationship = fields.Selection([
        ('spouse', 'Spouse'),
        ('business', 'Business Partner'),
        ('other', 'Other')
    ], string="Relationship")


class FinanceContract(models.Model):
    _name = 'finance.contract'
    _description = 'Financial Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'agreement_no'

    company_id = fields.Many2one('res.company', string='Company', required=True, 
                        default=lambda self: self.env.company, index=True)

    # 1. APPLICATION TYPE (HP/Floor Stock)
    application_type = fields.Selection([
        ('hp', 'Hire Purchase'),
        ('floor_stock', 'Floor Stock'),
        ('lease', 'Leasing'),
        ('other', 'Other')
    ], string="Application Type", default='hp', required=True)
    
    # 2. SALESPERSON (External Agent/Client)
    #   "Select from Client", implying this is an external partner/broker
    sales_agent_id = fields.Many2one('res.partner', string="Salesperson (Agent)",
                                     domain="[('finance_partner_type', '=', 'broker'), ('active', '=', True)]",
                                     help="The external salesperson or broker associated with this deal.")
    
    # 3. INSURER
    insurer_id = fields.Many2one('res.partner', string="Insurer",
                                 domain="[('finance_partner_type', '=', 'insurer')]")
    
    # --- Header Info ---
    hp_ac_no = fields.Char(string="HP A/C No.")

    product_id = fields.Many2one('finance.product', string="Financial Product",
        domain="[('active', '=', True)]", required=True)

    # Helper to control UI visibility (hides/shows Leasing fields)
    product_type = fields.Selection(related='product_id.product_type', string="Product Type", store=True)

    asset_id = fields.Many2one('finance.asset', string="Asset", required=True)
    asset_reg_no = fields.Char(related='asset_id.vehicle_id.license_plate', string="Asset Reg No.", store=True)
    asset_make = fields.Char(related='asset_id.vehicle_id.model_id.brand_id.name', string="Make", store=True)
    asset_model = fields.Char(related='asset_id.vehicle_id.model_id.name', string="Model", store=True)
    asset_type = fields.Selection(related='asset_id.asset_type', string="Asset Type", store=True)

    asset_condition = fields.Selection([
        ('new', 'New'),
        ('used', 'Used'),
        ('demo', 'Demonstrator')
    ], string="Asset Condition", required=True, default='new')


    hirer_id = fields.Many2one('res.partner', string="Hirer's Name", required=True, tracking=True,
                               domain="[('finance_partner_type', 'in', [False, '']), ('finance_blacklist', '=', False)]",
                               help="Select the individual or company hiring the asset (not a broker/insurer/finance company/supplier).")
    ic_no = fields.Char(related='hirer_id.vat', string="ID / IC No.", readonly=False)

    agreement_date = fields.Date(string="Agreement Date", default=fields.Date.context_today)
    agreement_no = fields.Char(string="Agreement No", required=True, copy=False, default='New')

    finance_company_id = fields.Many2one('res.partner', string="Finance Name",
                                         domain="[('finance_partner_type', '=', 'finance_company')]")
    submit_date = fields.Date(string="Submit Date")
    entry_date = fields.Date(string="Entry Date", default=fields.Date.context_today)
    inst_day = fields.Integer(string="Inst. Day (1-31)")
    multi_purch = fields.Boolean(string="Multi Purch")
    mortgage = fields.Boolean(string="Mortgage")
    advanced_payment = fields.Monetary(string="Advanced Payment", currency_field='currency_id')
    bank_acct = fields.Char(string="Bank Account")

    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly')
    ], string="Period Type", default='monthly')

    ac_status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('repo', 'Repossessed')
    ], string="A/C Status", default='draft', tracking=True)

    late_status = fields.Selection([
        ('normal', 'Normal'),
        ('attention', 'Attention'),
        ('legal', 'Legal Action')
    ], string="Late Status", default='normal')

    cal_period = fields.Integer(string="Cal Period")
    entry_staff_id = fields.Many2one('res.users', string="Entry Staff", default=lambda self: self.env.user)
    installment_type = fields.Selection([
        ('level', 'Level Principal'),
        ('annuity', 'Annuity/Standard')
    ], string="Installment Type")

    installment_pattern = fields.Selection([
        ('normal', 'Normal'),
        ('front', 'Front Loaded'),
        ('average', 'Average')
    ], string="Instalment Pattern", default='normal')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # --- Financials ---
    is_hp_act = fields.Boolean(string="HP Act (<$55k)", compute='_compute_hp_act', store=True,
                               help="Automatically checked if Loan Amount is $55,000 or less.")

    interest_type = fields.Selection([
        ('flat', 'Flat Rate'),
        ('effective', 'Effective Rate') 
    ], string="Interest Type", default='flat', 
       help="Effective Rate usually implies standard amortization/annuity.")
    
    interest_method = fields.Selection([
        ('flat', 'Flat Rate (Straight Line)'),
        ('rule78', 'Rule of 78 (Sum of Digits)')
    ], string="Interest Method", default='rule78', required=True,
       help="Method used to allocate interest across installments.")

    payment_scheme = fields.Selection([
        ('arrears', 'Arrears (Normal)'),
        ('advance', 'Advance (Front Payment)')
    ], string="Payment Scheme", default='arrears', required=True,
       help="Arrears: 1st payment is due 1 month after start.\nAdvance: 1st payment is collected immediately.")

    cash_price = fields.Monetary(string="Cash Price")
    down_payment = fields.Monetary(string="Down Payment")

    loan_amount = fields.Monetary(string="Loan Amount", compute='_compute_financials', store=True, tracking=True)
    int_rate_pa = fields.Float(string="Int Rate P.A.%", tracking=True)
    no_of_inst = fields.Many2one('finance.term', string="No. of Inst.", tracking=True)

    term_charges = fields.Monetary(string="Term Charges", compute='_compute_financials', store=True, readonly=False)
    balance_hire = fields.Monetary(string="Balance Hire (P + I)", compute='_compute_financials', store=True)

    first_inst_amount = fields.Monetary(string="First Inst.", compute='_compute_installment_amounts', store=True, readonly=False)
    monthly_inst = fields.Monetary(string="Monthly Inst.", compute='_compute_installment_amounts', store=True, readonly=False)
    last_inst_amount = fields.Monetary(string="Last Inst.", compute='_compute_installment_amounts', store=True, readonly=False)

    # --- Leasing Specifics (Hidden for HP) ---
    residual_value_percent = fields.Float(string="Residual Value (%)")
    residual_value = fields.Monetary(string="Residual Value (RV)")

    mileage_limit = fields.Integer(string="Annual Mileage Limit (km)")
    excess_mileage_rate = fields.Monetary(string="Excess Mileage Rate")

    supplier_id = fields.Many2one('res.partner', string="Supplier / Dealer",
                                  domain="[('finance_partner_type', '=', 'supplier')]")
    supplier_code = fields.Char(related='supplier_id.ref', string="Supplier Code", readonly=False)
    commission = fields.Monetary(string="Commission")

    admin_fee_id = fields.Many2one('finance.charge', string="Admin Fee Config", domain=[('type', '=', 'admin')])
    admin_fee = fields.Monetary(string="Admin Fee")
    other_cost_id = fields.Many2one('finance.charge', string="Other Cost Config", domain=[('type', '=', 'other')])
    other_cost = fields.Monetary(string="Other Cost")

    # --- Tracking ---
    no_inst_paid = fields.Integer(string="No. of Inst. Paid", compute='_compute_payment_status', store=True)
    total_inst_paid = fields.Monetary(string="Total Installment Paid", compute='_compute_payment_status', store=True)
    total_late_paid = fields.Monetary(string="Total Late Paid", default=0.0)
    balance_installment = fields.Monetary(string="Balance Installment", compute='_compute_balances')
    last_record_date = fields.Date(string="Last Record Date")

    os_balance = fields.Monetary(string="O/S Balance", compute='_compute_balances')
    balance_late_charges = fields.Monetary(string="Balance Late Charges")
    balance_misc_fee = fields.Monetary(string="Balance Misc Fee")
    total_payable = fields.Monetary(string="Total Payable", compute='_compute_balances')
    next_inst_date = fields.Date(string="Next Inst. Date")

    collection_bank_id = fields.Many2one('res.bank', string="Collection Bank ID")

    # --- Misc ---
    first_due_date = fields.Date(string="First Due Date")
    reference_no = fields.Char(string="Reference No")
    block_disc_no = fields.Char(string="Block Disc No.")
    last_inst_date = fields.Date(string="Last Inst. Date")
    maturity_date = fields.Date(string="Maturity Date", compute='_compute_maturity_date', store=True)

    interest_derived = fields.Monetary(string="Interest Derived")
    block_status = fields.Boolean(string="Block Status")

    search_fee = fields.Monetary(string="Search Fee")
    reminder_fee = fields.Monetary(string="Reminder Fee")
    schedule_4_fee = fields.Monetary(string="4th Schedule Fee")
    schedule_5_fee = fields.Monetary(string="5th Schedule Fee")
    warning_letter_fee = fields.Monetary(string="Warning Letter Fee")
    final_letter_fee = fields.Monetary(string="Final Letter Fee")

    journal_id = fields.Many2one('account.journal', string="Invoicing Journal", domain=[('type','=','sale')], required=True)
    asset_account_id = fields.Many2one('account.account', string="Principal/Asset Account", required=True)
    income_account_id = fields.Many2one('account.account', string="Interest Income Account", required=True)
    unearned_interest_account_id = fields.Many2one('account.account', string="Unearned Interest Account",
        help="Credit account for interest at disbursement (Liability/Contra-Asset)", required=True)

    line_ids = fields.One2many('finance.contract.line', 'contract_id', string="Installments")

    payment_count = fields.Integer(compute='_compute_payment_count', string="Payment Count")
    invoice_count = fields.Integer(compute='_compute_invoice_count', string="Invoice Count")

    # Penalty Rule
    penalty_rule_id = fields.Many2one('finance.penalty.rule', string="Penalty Rule")

    total_overdue_days = fields.Integer(string="Days Overdue", compute='_compute_overdue_status', store=True)
    accrued_penalty = fields.Monetary(string="Accrued Penalty", currency_field='currency_id', default=0.0)

    # 1. GUARANTORS (Multiple)
    guarantor_line_ids = fields.One2many('finance.contract.guarantor', 'contract_id', string="Guarantors")

    # 2. CO-BORROWERS / JOINT HIRERS (Multiple)
    joint_hirer_line_ids = fields.One2many('finance.contract.joint.hirer', 'contract_id', string="Co-Borrowers")

    # --- Disbursement & Notices Tracking ---
    disbursement_move_id = fields.Many2one('account.move', string="Disbursement Entry", readonly=True)

    date_reminder_sent = fields.Date(string="Reminder Notice Date", readonly=True)
    date_4th_sched_sent = fields.Date(string="4th Schedule Date", readonly=True)
    date_repo_order = fields.Date(string="Repossession Date", readonly=True)
    date_5th_sched_sent = fields.Date(string="5th Schedule Date", readonly=True)

    # --- Core Logic ---

    @api.depends('loan_amount')
    def _compute_hp_act(self):
        """Determine if HP Act applies based on configurable limit"""
        for rec in self:
            hp_limit = self.env['ir.config_parameter'].sudo().get_param('asset_finance.hp_act_limit', default=55000.0)
            rec.is_hp_act = (rec.loan_amount <= float(hp_limit))

    @api.depends('first_due_date', 'no_of_inst')
    def _compute_maturity_date(self):
        """Calculate contract maturity date"""
        from dateutil.relativedelta import relativedelta
        for rec in self:
            if rec.first_due_date and rec.no_of_inst:
                rec.maturity_date = rec.first_due_date + relativedelta(months=rec.no_of_inst.months - 1)
            else:
                rec.maturity_date = False

    @api.onchange('interest_type')
    def _onchange_interest_type(self):
        """Map CSV Interest Type to Internal Calculation Method"""
        if self.interest_type == 'flat':
            self.interest_method = 'flat' # Uses existing logic
        elif self.interest_type == 'effective':
            self.installment_type = 'annuity' # Uses standard amortization
            
    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.no_of_inst = False # Reset term when product changes
            self.penalty_rule_id = self.product_id.default_penalty_rule_id
            # Auto-fill defaults from the Product itself
            self.int_rate_pa = self.product_id.default_int_rate
            self.residual_value_percent = self.product_id.default_rv_percentage
            self.mileage_limit = self.product_id.annual_mileage_limit
            self.excess_mileage_rate = self.product_id.excess_mileage_charge
            self._onchange_rv_percent()

            # --- New Domain Logic ---
            prod = self.product_id
            term_domain = []
            if prod.min_months and prod.max_months and prod.step_months > 0:
                valid_months = list(range(prod.min_months, prod.max_months + 1, prod.step_months))
                term_domain = [('months', 'in', valid_months)]
            else:
                # Fallback to default if no rules are set on the product
                default_months = list(range(12, 121, 12))
                term_domain = [('months', 'in', default_months)]

            return {'domain': {'no_of_inst': term_domain}}

        # If no product is selected, don't show any options to force selection first
        return {'domain': {'no_of_inst': [('id', '=', False)]}}

    @api.onchange('residual_value_percent', 'cash_price')
    def _onchange_rv_percent(self):
        if self.residual_value_percent and self.cash_price:
            self.residual_value = self.cash_price * (self.residual_value_percent / 100)

    @api.onchange('admin_fee_id')
    def _onchange_admin_fee(self):
        if self.admin_fee_id:
            self.admin_fee = self.admin_fee_id.amount

    @api.onchange('other_cost_id')
    def _onchange_other_cost(self):
        if self.other_cost_id:
            self.other_cost = self.other_cost_id.amount

    # --- Validation Constraints ---

    @api.constrains('product_id', 'agreement_date')
    def _check_product_validity(self):
        for rec in self:
            if rec.product_id and rec.agreement_date:
                if rec.product_id.date_start and rec.agreement_date < rec.product_id.date_start:
                    raise ValidationError(f"Product not valid before {rec.product_id.date_start}.")
                if rec.product_id.date_end and rec.agreement_date > rec.product_id.date_end:
                    raise ValidationError(f"Product expired on {rec.product_id.date_end}.")

    @api.constrains('down_payment', 'cash_price')
    def _check_down_payment(self):
        """Validate down payment does not exceed cash price"""
        for rec in self:
            if rec.down_payment > rec.cash_price:
                raise ValidationError(_("Down payment cannot exceed cash price."))

    @api.constrains('first_due_date', 'agreement_date')
    def _check_first_due_date(self):
        """Validate first due date is not before agreement date"""
        for rec in self:
            if rec.first_due_date and rec.agreement_date and rec.first_due_date < rec.agreement_date:
                raise ValidationError(_("First due date cannot be before agreement date."))

    @api.constrains('int_rate_pa')
    def _check_interest_rate(self):
        """Validate interest rate is reasonable"""
        for rec in self:
            if rec.int_rate_pa < 0:
                raise ValidationError(_("Interest rate cannot be negative."))
            if rec.int_rate_pa > 100:
                raise ValidationError(_("Interest rate cannot exceed 100%."))

    @api.constrains('residual_value_percent')
    def _check_residual_value(self):
        """Validate residual value percentage"""
        for rec in self:
            if rec.residual_value_percent < 0 or rec.residual_value_percent > 100:
                raise ValidationError(_("Residual value percentage must be between 0 and 100."))

    # --- CRUD Operations ---

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('agreement_no', 'New') == 'New':
                vals['agreement_no'] = self.env['ir.sequence'].next_by_code('finance.contract') or 'New'
        return super(FinanceContract, self).create(vals_list)

    def write(self, vals):
        trigger_fields = {
            'cash_price', 'down_payment', 'int_rate_pa', 'no_of_inst',
            'first_inst_amount', 'monthly_inst', 'last_inst_amount',
            'interest_method', 'payment_scheme', 'first_due_date'
        }
        res = super().write(vals)
        if self.env.context.get('skip_schedule_generation'):
            return res
        if any(f in vals for f in trigger_fields):
            for rec in self:
                if rec.line_ids:
                    rec.with_context(skip_schedule_generation=True).action_generate_schedule()
        return res

    # --- Computed Fields ---

    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = self.env['account.payment'].search_count([('contract_id', '=', rec.id)])

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count([
                ('invoice_origin', '=', rec.agreement_no),
                ('move_type', '=', 'out_invoice')
            ])

    @api.depends('line_ids.invoice_id.payment_state')
    def _compute_payment_status(self):
        for rec in self:
            paid_lines = rec.line_ids.filtered(lambda l: l.invoice_id.payment_state in ['paid', 'in_payment'])
            rec.no_inst_paid = len(paid_lines)
            rec.total_inst_paid = sum(paid_lines.mapped('amount_total'))

    @api.depends('balance_hire', 'total_inst_paid', 'balance_late_charges', 'balance_misc_fee')
    def _compute_balances(self):
        for rec in self:
            rec.balance_installment = rec.balance_hire - rec.total_inst_paid
            rec.os_balance = rec.balance_installment
            rec.total_payable = rec.os_balance + rec.balance_late_charges + rec.balance_misc_fee

    # --- Status Actions ---

    def action_approve(self):
        for rec in self:
            rec.ac_status = 'active'

    def action_close(self):
        for rec in self:
            rec.ac_status = 'closed'

    def action_draft(self):
        for rec in self:
            rec.ac_status = 'draft'

    # --- View Actions ---

    def action_view_payments(self):
        self.ensure_one()
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id}
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('invoice_origin', '=', self.agreement_no)],
        }
