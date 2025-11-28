from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class VehicleAsset(models.Model):
    _name = 'leasing.vehicle'
    _description = 'Vehicle Asset'
    _rec_name = 'reg_no'

    make = fields.Char(string="Make", required=True)
    model = fields.Char(string="Model", required=True)
    reg_no = fields.Char(string="Registration No.", required=True, unique=True)
    engine_no = fields.Char(string="Engine No.")
    chassis_no = fields.Char(string="Chassis No.")
    year = fields.Integer(string="Year of Manufacture")
    color = fields.Char(string="Color")
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
    ], string="Fuel Type")
    status = fields.Selection([
        ('available', 'Available'),
        ('leased', 'Leased'),
        ('maintenance', 'Maintenance'),
        ('sold', 'Sold')
    ], string="Asset Status", default='available')

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.reg_no} - {record.make} {record.model}"
            result.append((record.id, name))
        return result

class LeasingDealer(models.Model):
    _name = 'leasing.dealer'
    _description = 'Dealer Information'

    name = fields.Char(string="Dealer Name", required=True)
    code = fields.Char(string="Dealer Code", required=True)
    active = fields.Boolean(default=True)

class LeasingCharge(models.Model):
    _name = 'leasing.charge'
    _description = 'Standard Charges and Fees'

    name = fields.Char(string="Charge Name", required=True)
    amount = fields.Float(string="Default Amount")
    type = fields.Selection([
        ('admin', 'Admin Fee'),
        ('other', 'Other Cost'),
        ('penalty', 'Penalty')
    ], required=True)

class LeasingContract(models.Model):
    _name = 'leasing.contract'
    _description = 'Financial Contract (HP & Leasing)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'agreement_no'

    # --- Tab A: Main ---
    hp_ac_no = fields.Char(string="HP A/C No.")
    vehicle_id = fields.Many2one('leasing.vehicle', string="Vehicle Asset", required=True)
    
    # Related fields from Vehicle Asset
    vehicle_reg_no = fields.Char(related='vehicle_id.reg_no', string="Vehicle Reg No.", store=True)
    make = fields.Char(related='vehicle_id.make', string="Make", store=True)
    model = fields.Char(related='vehicle_id.model', string="Model", store=True)

    hirer_id = fields.Many2one('res.partner', string="Hirer's Name", required=True)
    ic_no = fields.Char(related='hirer_id.vat', string="ID / IC No.", readonly=False) # Assuming VAT field is used for ID
    
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

    # --- Tab B: Finance Info ---
    cash_price = fields.Monetary(string="Cash Price")
    down_payment = fields.Monetary(string="Down Payment")
    
    # Calculated: Loan Amount
    loan_amount = fields.Monetary(string="Loan Amount", compute='_compute_financials', store=True)
    
    int_rate_pa = fields.Float(string="Int Rate P.A.%")
    no_of_inst = fields.Integer(string="No. of Inst.")
    
    term_charges = fields.Monetary(string="Term Charges", compute='_compute_financials', store=True, readonly=False)
    balance_hire = fields.Monetary(string="Balance Hire (P + I)", compute='_compute_financials', store=True)
    
    first_inst_amount = fields.Monetary(string="First Inst.")
    monthly_inst = fields.Monetary(string="Monthly Inst.")
    last_inst_amount = fields.Monetary(string="Last Inst.")
    
    dealer_id = fields.Many2one('leasing.dealer', string="Dealer")
    dealer_code = fields.Char(related='dealer_id.code', string="Dealer Code")
    dealer_name = fields.Char(related='dealer_id.name', string="Dealer Name")
    
    commission = fields.Monetary(string="Commission")
    
    admin_fee_id = fields.Many2one('leasing.charge', string="Admin Fee Config", domain=[('type', '=', 'admin')])
    admin_fee = fields.Monetary(string="Admin Fee")
    
    other_cost_id = fields.Many2one('leasing.charge', string="Other Cost Config", domain=[('type', '=', 'other')])
    other_cost = fields.Monetary(string="Other Cost")

    @api.depends('cash_price', 'down_payment', 'int_rate_pa', 'no_of_inst')
    def _compute_financials(self):
        for rec in self:
            rec.loan_amount = rec.cash_price - rec.down_payment
            # Simple Flat Rate logic for example purposes
            interest = (rec.loan_amount * (rec.int_rate_pa / 100) * (rec.no_of_inst / 12)) if rec.no_of_inst else 0
            rec.term_charges = interest
            rec.balance_hire = rec.loan_amount + interest

    @api.onchange('admin_fee_id')
    def _onchange_admin_fee(self):
        if self.admin_fee_id:
            self.admin_fee = self.admin_fee_id.amount

    @api.onchange('other_cost_id')
    def _onchange_other_cost(self):
        if self.other_cost_id:
            self.other_cost = self.other_cost_id.amount

    # --- Tab C: Paid (Calculated Placeholder) ---
    # In a real app, these would compute from a related 'payment.history' model
    no_inst_paid = fields.Integer(string="No. of Inst. Paid", default=0)
    total_inst_paid = fields.Monetary(string="Total Installment Paid", default=0.0)
    total_late_paid = fields.Monetary(string="Total Late Paid", default=0.0)
    balance_installment = fields.Monetary(string="Balance Installment", compute='_compute_balances')
    last_record_date = fields.Date(string="Last Record Date")

    # --- Tab D: O/S (Outstanding) ---
    os_balance = fields.Monetary(string="O/S Balance", compute='_compute_balances')
    balance_late_charges = fields.Monetary(string="Balance Late Charges")
    balance_misc_fee = fields.Monetary(string="Balance Misc Fee")
    total_payable = fields.Monetary(string="Total Payable", compute='_compute_balances')
    next_inst_date = fields.Date(string="Next Inst. Date")

    @api.depends('balance_hire', 'total_inst_paid', 'balance_late_charges', 'balance_misc_fee')
    def _compute_balances(self):
        for rec in self:
            rec.balance_installment = rec.balance_hire - rec.total_inst_paid
            rec.os_balance = rec.balance_installment # Simplified logic
            rec.total_payable = rec.os_balance + rec.balance_late_charges + rec.balance_misc_fee

    # --- Tab E: Giro Application ---
    collection_bank_id = fields.Many2one('res.bank', string="Collection Bank ID")

    # --- Tab F: Misc ---
    first_due_date = fields.Date(string="First Due Date")
    agreement_type = fields.Selection([('hp', 'Hire Purchase'), ('lease', 'Leasing')], string="Agreement Type")
    reference_no = fields.Char(string="Reference No")
    block_disc_no = fields.Char(string="Block Disc No.")
    last_inst_date = fields.Date(string="Last Inst. Date")
    
    interest_derived = fields.Monetary(string="Interest Derived")
    block_status = fields.Boolean(string="Block Status")
    
    # Fees
    search_fee = fields.Monetary(string="Search Fee")
    reminder_fee = fields.Monetary(string="Reminder Fee")
    schedule_4_fee = fields.Monetary(string="4th Schedule Fee")
    schedule_5_fee = fields.Monetary(string="5th Schedule Fee")
    warning_letter_fee = fields.Monetary(string="Warning Letter Fee")
    final_letter_fee = fields.Monetary(string="Final Letter Fee")

    def action_pay_type(self):
        """ Button Action for PAYTYPE """
        # Logic to open payment wizard or change payment type
        return {'type': 'ir.actions.client', 'tag': 'reload'}