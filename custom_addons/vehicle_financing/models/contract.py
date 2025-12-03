from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class LeasingContract(models.Model):
    _name = 'leasing.contract'
    _description = 'Financial Contract (HP & Leasing)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'agreement_no'

    # --- Header Info ---
    hp_ac_no = fields.Char(string="HP A/C No.")
    
    product_id = fields.Many2one('leasing.product', string="Financial Product", 
        domain="[('active', '=', True)]", required=True)

    # Helper to control UI visibility (hides/shows Leasing fields)
    product_type = fields.Selection(related='product_id.product_type', string="Product Type", store=True)

    vehicle_id = fields.Many2one('leasing.vehicle', string="Vehicle Asset", required=True)
    vehicle_reg_no = fields.Char(related='vehicle_id.reg_no', string="Vehicle Reg No.", store=True)
    make = fields.Char(related='vehicle_id.make', string="Make", store=True)
    model = fields.Char(related='vehicle_id.model', string="Model", store=True)

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
    cash_price = fields.Monetary(string="Cash Price")
    down_payment = fields.Monetary(string="Down Payment")
    
    loan_amount = fields.Monetary(string="Loan Amount", compute='_compute_financials', store=True)
    int_rate_pa = fields.Float(string="Int Rate P.A.%")
    no_of_inst = fields.Integer(string="No. of Inst.")
    
    term_charges = fields.Monetary(string="Term Charges", compute='_compute_financials', store=True, readonly=False)
    balance_hire = fields.Monetary(string="Balance Hire (P + I)", compute='_compute_financials', store=True)
    
    first_inst_amount = fields.Monetary(string="First Inst.")
    monthly_inst = fields.Monetary(string="Monthly Inst.")
    last_inst_amount = fields.Monetary(string="Last Inst.")
    
    # --- Leasing Specifics (Hidden for HP) ---
    residual_value_percent = fields.Float(string="Residual Value (%)")
    residual_value = fields.Monetary(string="Residual Value (RV)")
    
    mileage_limit = fields.Integer(string="Annual Mileage Limit (km)")
    excess_mileage_rate = fields.Monetary(string="Excess Mileage Rate")

    dealer_id = fields.Many2one('leasing.dealer', string="Dealer")
    dealer_partner_id = fields.Many2one('res.partner', string="Dealer Partner Record")
    dealer_code = fields.Char(related='dealer_id.code', string="Dealer Code")
    dealer_name = fields.Char(related='dealer_id.name', string="Dealer Name")
    commission = fields.Monetary(string="Commission")
    
    admin_fee_id = fields.Many2one('leasing.charge', string="Admin Fee Config", domain=[('type', '=', 'admin')])
    admin_fee = fields.Monetary(string="Admin Fee")
    other_cost_id = fields.Many2one('leasing.charge', string="Other Cost Config", domain=[('type', '=', 'other')])
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

    line_ids = fields.One2many('leasing.contract.line', 'contract_id', string="Installments")
    
    payment_count = fields.Integer(compute='_compute_payment_count', string="Payment Count")
    invoice_count = fields.Integer(compute='_compute_invoice_count', string="Invoice Count")
    
    # --- Logic ---

    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            # Auto-fill defaults from the Product itself
            self.int_rate_pa = self.product_id.default_int_rate
            self.residual_value_percent = self.product_id.default_rv_percentage
            self.mileage_limit = self.product_id.annual_mileage_limit
            self.excess_mileage_rate = self.product_id.excess_mileage_charge
            self._onchange_rv_percent()

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
    
    @api.model
    def create(self, vals):
        if vals.get('agreement_no', 'New') == 'New':
            vals['agreement_no'] = self.env['ir.sequence'].next_by_code('leasing.contract') or 'New'
        return super(LeasingContract, self).create(vals)
    
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = self.env['account.payment'].search_count([('leasing_contract_id', '=', rec.id)])

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count([
                ('invoice_origin', '=', rec.agreement_no),
                ('move_type', '=', 'out_invoice')
            ])

    def action_generate_schedule(self):
        self.ensure_one()
        self.line_ids.unlink()
        
        if not self.no_of_inst or not self.monthly_inst:
            raise UserError("Please set Number of Installments and Monthly Installment amount.")

        start_date = self.first_due_date or fields.Date.today()
        lines = []
        monthly_principal_base = self.loan_amount / self.no_of_inst

        for i in range(1, self.no_of_inst + 1):
            date_due = start_date + relativedelta(months=i-1)
            principal = monthly_principal_base
            interest = self.monthly_inst - principal
            
            if i == self.no_of_inst:
                principal = self.loan_amount - sum(l[2]['amount_principal'] for l in lines)
                interest = self.monthly_inst - principal

            lines.append((0, 0, {
                'sequence': i,
                'date_due': date_due,
                'amount_principal': principal,
                'amount_interest': interest,
                'amount_total': self.monthly_inst,
            }))
            
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
                    'invoice_origin': rec.agreement_no,
                    'ref': f"Installment {line.sequence}/{rec.no_of_inst}",
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

    def action_pay_dealer(self):
        self.ensure_one()
        if not self.dealer_partner_id:
            raise UserError("Please select a Dealer Partner Record in the Finance Info tab before paying.")
        return {
            'name': 'Pay Dealer',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'context': {
                'default_payment_type': 'outbound',
                'default_partner_type': 'supplier',
                'default_partner_id': self.dealer_partner_id.id,
                'default_amount': self.loan_amount,
                'default_ref': f"Payout for {self.agreement_no}",
                'default_leasing_contract_id': self.id,
            }
        }
        
    def action_view_payments(self):
        self.ensure_one()
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('leasing_contract_id', '=', self.id)],
            'context': {'default_leasing_contract_id': self.id}
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