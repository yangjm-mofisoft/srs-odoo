from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Link the Payment to a Contract
    leasing_contract_id = fields.Many2one('leasing.contract', string="Leasing Contract", readonly=True)
    
    # Optional: Display vehicle info on the payment for easier search
    vehicle_reg_no = fields.Char(related='leasing_contract_id.vehicle_reg_no', string="Vehicle Reg", store=True)