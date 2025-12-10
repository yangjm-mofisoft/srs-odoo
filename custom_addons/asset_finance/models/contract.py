from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import math

class FinanceContractGuarantor(models.Model):
    _name = 'finance.contract.guarantor'
    _description = 'Guarantor Line'

    contract_id = fields.Many2one('finance.contract', string="Contract", ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Guarantor Name", required=True, 
                                 domain="[('is_finance_guarantor', '=', True)]")
    
    # --- 1. Pull Details from res.partner ---
    nric = fields.Char(related='partner_id.nric', string="NRIC / ID No", readonly=True)
    email = fields.Char(related='partner_id.email', readonly=True)
    phone = fields.Char(related='partner_id.phone', readonly=True)
    # DELETED: mobile = fields.Char(related='partner_id.mobile', readonly=True) <-- CAUSING ERROR
    
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
                                 domain="[('is_finance_joint_hirer', '=', True)]")
    
    # --- Pull Details from res.partner ---
    nric = fields.Char(related='partner_id.nric', string="NRIC / ID No", readonly=True)
    email = fields.Char(related='partner_id.email', readonly=True)
    phone = fields.Char(related='partner_id.phone', readonly=True)
    # DELETED: mobile = fields.Char(related='partner_id.mobile', readonly=True) <-- CAUSING ERROR
    
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

    hirer_id = fields.Many2one('res.partner', string="Hirer's Name", required=True)
    ic_no = fields.Char(related='hirer_id.vat', string="ID / IC No.", readonly=False)
    
    agreement_date = fields.Date(string="Agreement Date", default=fields.Date.context_today)
    agreement_no = fields.Char(string="Agreement No", required=True, copy=False, default='New')
    
    finance_company_id = fields.Many2one('res.partner', string="Finance Name")
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

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # --- Financials ---
    is_hp_act = fields.Boolean(string="HP Act (<$55k)", compute='_compute_hp_act', store=True,
                               help="Automatically checked if Loan Amount is $55,000 or less.")
    
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
    
    loan_amount = fields.Monetary(string="Loan Amount", compute='_compute_financials', store=True)
    int_rate_pa = fields.Float(string="Int Rate P.A.%")
    no_of_inst = fields.Many2one('finance.term', string="No. of Inst.")
    
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

    supplier_id = fields.Many2one('res.partner', string="Supplier / Dealer", domain="[('supplier_rank', '>', 0)]")
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
     # NEW: Unearned Interest Account (Liability)
    unearned_interest_account_id = fields.Many2one('account.account', string="Unearned Interest Account", 
        help="Credit account for interest at disbursement (Liability/Contra-Asset)", required=True)

    #  Link to Journal Entry instead of Payment
    #disbursement_id = fields.Many2one('account.payment', string="Disbursement Voucher", readonly=True)
    disbursement_move_id = fields.Many2one('account.move', string="Disbursement Entry", readonly=True)
    
    date_reminder_sent = fields.Date(string="Reminder Notice Date", readonly=True)
    date_4th_sched_sent = fields.Date(string="4th Schedule Date", readonly=True)
    date_repo_order = fields.Date(string="Repossession Date", readonly=True)
    date_5th_sched_sent = fields.Date(string="5th Schedule Date", readonly=True)
    # --- Logic ---
    
    @api.depends('loan_amount')
    def _compute_hp_act(self):
        # Requirement: HP Act applies if Financed Amount <= 55,000
        limit = 55000.0  # Ideally, move this to System Parameters later
        for rec in self:
            rec.is_hp_act = (rec.loan_amount <= limit)
    
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

    @api.constrains('product_id', 'agreement_date')
    def _check_product_validity(self):
        for rec in self:
            if rec.product_id and rec.agreement_date:
                if rec.product_id.date_start and rec.agreement_date < rec.product_id.date_start:
                    raise ValidationError(f"Product not valid before {rec.product_id.date_start}.")
                if rec.product_id.date_end and rec.agreement_date > rec.product_id.date_end:
                    raise ValidationError(f"Product expired on {rec.product_id.date_end}.")
    
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

    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = self.env['account.payment'].search_count([('contract_id', '=', rec.id)])

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count([
                ('invoice_origin', '=', rec.agreement_no),
                ('move_type', '=', 'out_invoice')
            ])

    # --------------------------------------------------------
    # LOGIC UPDATE: SCHEDULE GENERATION (RULE OF 78)
    # --------------------------------------------------------
    def action_generate_schedule(self):
        self.ensure_one()
        self.line_ids.unlink()
        
        if not self.no_of_inst or not self.monthly_inst:
            raise UserError("Please set Number of Installments and Monthly Installment amount.")

        # 1. Determine Start Date based on Payment Scheme
        start_date = self.first_due_date
        if not start_date:
            base_date = self.agreement_date or fields.Date.today()
            if self.payment_scheme == 'advance':
                # Front payment: Due immediately on agreement date
                start_date = base_date
            else:
                # Normal arrears: Due 1 month after
                start_date = base_date + relativedelta(months=1)

        lines = []
        
        # 2. Setup Variables for Calculation
        n = self.no_of_inst.months
        total_principal = self.loan_amount
        total_interest = self.term_charges
        monthly_inst = self.monthly_inst
        
        # Rule of 78 Denominator: Sum of Digits = n * (n + 1) / 2
        # Example: For 12 months, SOD = 78.
        sum_of_digits = (n * (n + 1)) / 2 if self.interest_method == 'rule78' else 0
        
        # Trackers for rounding adjustments
        allocated_principal = 0.0
        allocated_interest = 0.0

        for i in range(1, n + 1):
            date_due = start_date + relativedelta(months=i-1)
            
            # --- A. Interest Calculation ---
            if self.interest_method == 'rule78':
                # Rule of 78 Formula: 
                # Interest_k = Total_Interest * (Remaining_Months / Sum_of_Digits)
                # For month 1 of 12, Remaining weight is 12. For month 12, it is 1.
                weight = n - i + 1
                interest_portion = total_interest * (weight / sum_of_digits)
            else:
                # Flat Rate: Evenly distributed
                interest_portion = total_interest / n
            
            # Rounding to 2 decimal places is crucial for currency
            interest_portion = round(interest_portion, 2)
            
            # --- B. Principal Calculation ---
            # Determine the installment amount for this specific line
            if i == 1:
                amount_total = self.first_inst_amount
            else:
                amount_total = self.monthly_inst

            principal_portion = monthly_inst - interest_portion
            
            # --- C. Final Installment Adjustment ---
            if i == n:
                principal_portion = total_principal - allocated_principal
                interest_portion = total_interest - allocated_interest
                amount_total = principal_portion + interest_portion

            # Append the line
            lines.append((0, 0, {
                'sequence': i,
                'date_due': date_due,
                'amount_principal': principal_portion,
                'amount_interest': interest_portion,
                'amount_total': amount_total,
            }))
            
            # Update trackers
            allocated_principal += principal_portion
            allocated_interest += interest_portion
            
        self.write({'line_ids': lines})

    def action_create_invoices(self):
        for rec in self:
            due_lines = rec.line_ids.filtered(lambda l: not l.invoice_id and l.date_due <= fields.Date.today())
            if not due_lines:
                raise UserError(_("No installments are due for invoicing today."))

            for line in due_lines:
                invoice_lines = []
                invoice_lines.append((0, 0, {
                    'name': f"Principal Repayment (Inst #{line.sequence})",
                    'quantity': 1,
                    'price_unit': line.amount_principal,
                    'account_id': rec.asset_account_id.id, 
                }))

                if line.amount_interest > 0:
                    invoice_lines.append((0, 0, {
                        'name': f"Interest Charges (Inst #{line.sequence})",
                        'quantity': 1,
                        'price_unit': line.amount_interest,
                        'account_id': rec.income_account_id.id,
                        'tax_ids': []
                    }))

                invoice = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': rec.hirer_id.id,
                    'invoice_date': line.date_due,
                    'date': line.date_due,
                    'journal_id': rec.journal_id.id,
                    'invoice_origin': rec.agreement_no, # Used for invoice stat button
                    'ref': f"Installment {line.sequence}/{rec.no_of_inst.months}",
                    'invoice_line_ids': invoice_lines,
                })
                
                line.invoice_id = invoice.id
                invoice.action_post()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Success', 'message': f'{len(due_lines)} Invoices created!', 'type': 'success'}
            }

    @api.depends('line_ids.invoice_id.payment_state')
    def _compute_payment_status(self):
        for rec in self:
            paid_lines = rec.line_ids.filtered(lambda l: l.invoice_id.payment_state in ['paid', 'in_payment'])
            rec.no_inst_paid = len(paid_lines)
            rec.total_inst_paid = sum(paid_lines.mapped('amount_total'))

    @api.depends('cash_price', 'down_payment', 'int_rate_pa', 'no_of_inst')
    def _compute_financials(self):
        for rec in self:
            rec.loan_amount = rec.cash_price - rec.down_payment
            months = rec.no_of_inst.months if rec.no_of_inst else 0
            interest = (rec.loan_amount * (rec.int_rate_pa / 100) * (months / 12)) if months else 0
            rec.term_charges = interest
            rec.balance_hire = rec.loan_amount + interest

    @api.depends('loan_amount', 'int_rate_pa', 'no_of_inst')
    def _compute_installment_amounts(self):
        """
        Automatically computes the installment amounts based on the annuity formula.
        The fields remain editable for manual overrides.
        """
        for rec in self:
            if rec.no_of_inst and rec.no_of_inst.months > 0 and rec.loan_amount > 0:
                n = rec.no_of_inst.months
                if rec.int_rate_pa > 0:
                    # Standard annuity formula for level payments
                    P = rec.loan_amount
                    # Monthly interest rate
                    r = (rec.int_rate_pa / 100) / 12
                    
                    # M = P * [r(1+r)^n] / [(1+r)^n - 1]
                    try:
                        monthly_inst = P * (r * (1 + r)**n) / ((1 + r)**n - 1)
                    except ZeroDivisionError:
                        monthly_inst = rec.loan_amount / n
                else:
                    # No interest, just divide principal by number of installments
                    monthly_inst = rec.loan_amount / n
                
                rounded_inst = math.floor(monthly_inst)
                rec.first_inst_amount = rounded_inst
                rec.monthly_inst = rounded_inst
                if n > 1:
                    rec.last_inst_amount = rec.balance_hire - (rounded_inst * (n - 1))
                else:
                    rec.last_inst_amount = rec.balance_hire
            else:
                rec.monthly_inst = rec.first_inst_amount = rec.last_inst_amount = 0

    @api.onchange('admin_fee_id')
    def _onchange_admin_fee(self):
        if self.admin_fee_id:
            self.admin_fee = self.admin_fee_id.amount

    @api.onchange('other_cost_id')
    def _onchange_other_cost(self):
        if self.other_cost_id:
            self.other_cost = self.other_cost_id.amount

    @api.depends('balance_hire', 'total_inst_paid', 'balance_late_charges', 'balance_misc_fee')
    def _compute_balances(self):
        for rec in self:
            rec.balance_installment = rec.balance_hire - rec.total_inst_paid
            rec.os_balance = rec.balance_installment 
            rec.total_payable = rec.os_balance + rec.balance_late_charges + rec.balance_misc_fee

    def action_approve(self):
        for rec in self:
            rec.ac_status = 'active'

    def action_close(self):
        for rec in self:
            rec.ac_status = 'closed'

    def action_draft(self):
        for rec in self:
            rec.ac_status = 'draft'

     # --- Disbursement Logic ---
    def action_disburse(self):
        self.ensure_one()
        if self.disbursement_move_id:
            raise UserError("Disbursement Entry already created!")
        
        return {
            'name': 'Disbursement',
            'type': 'ir.actions.act_window',
            'res_model': 'finance.disbursement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id, 'active_id': self.id}
        }
    
    
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
    
    # -------------------------------------------------------------------------
    # PENALTY & OVERDUE LOGIC (Add this to models/contract.py)
    # -------------------------------------------------------------------------

    @api.depends('line_ids.date_due', 'line_ids.invoice_id.payment_state')
    def _compute_overdue_status(self):
        today = fields.Date.today()
        for rec in self:
            # Find the oldest unpaid line that is overdue
            overdue_lines = rec.line_ids.filtered(
                lambda l: l.date_due and l.date_due < today and l.invoice_id.payment_state != 'paid'
            )
            
            if overdue_lines:
                # Get the earliest due date
                earliest_due = min(overdue_lines.mapped('date_due'))
                delta = (today - earliest_due).days
                rec.total_overdue_days = delta
                
                # Auto-update Late Status based on days
                if delta > 90:
                    rec.late_status = 'legal'
                elif delta > 30:
                    rec.late_status = 'attention'
                else:
                    rec.late_status = 'normal'
            else:
                rec.total_overdue_days = 0
                rec.late_status = 'normal'

    # Action to open Early Settlement Wizard
    def action_early_settlement(self):
        self.ensure_one()
        return {
            'name': 'Early Settlement',
            'type': 'ir.actions.act_window',
            'res_model': 'finance.settlement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id, 'active_id': self.id}
        }
    
    # Cron Job to calculate late interest penalties
    def _cron_calculate_late_interest(self):
        """ Run nightly to calculate penalties based on the selected Rule """
        # Ensure we only check active contracts that have a rule assigned
        active_contracts = self.search([('ac_status', '=', 'active'), ('penalty_rule_id', '!=', False)])
        today = fields.Date.today()
        
        for contract in active_contracts:
            rule = contract.penalty_rule_id
            penalty_amount = 0.0
            
            # Find overdue lines
            overdue_lines = contract.line_ids.filtered(
                lambda l: l.date_due and l.date_due < today and l.invoice_id.payment_state != 'paid'
            )
            
            for line in overdue_lines:
                days_late = (today - line.date_due).days
                
                # Check Grace Period
                if days_late <= rule.grace_period_days:
                    continue

                if rule.method == 'daily_percent':
                    # Logic: (Principal * Rate / 100) / 365
                    daily_rate = (rule.rate / 100) / 365
                    daily_penalty = line.amount_principal * daily_rate
                    penalty_amount += daily_penalty
                    
                # You can implement other methods (fixed_one_time) here later

            # Update the balance
            if penalty_amount > 0:
                contract.accrued_penalty += penalty_amount
                contract.balance_late_charges = contract.accrued_penalty - contract.total_late_paid

    # --- Notices & Repossession Actions ---
    def action_send_reminder(self):
        self.ensure_one()
        self.date_reminder_sent = fields.Date.today()
        self.message_post(body="Reminder Notice Sent to Hirer.")

    def action_send_4th_schedule(self):
        self.ensure_one()
        self.date_4th_sched_sent = fields.Date.today()
        self.message_post(body="4th Schedule Notice Issued.")

    def action_issue_repo_order(self):
        self.ensure_one()
        self.date_repo_order = fields.Date.today()
        self.ac_status = 'repo'
        self.asset_id.status = 'repo'
        self.message_post(body="Repossession Order Issued. Contract status updated to Repossessed.")

    def action_send_5th_schedule(self):
        self.ensure_one()
        self.date_5th_sched_sent = fields.Date.today()
        self.message_post(body="5th Schedule Notice Issued (Post-Repossession).")