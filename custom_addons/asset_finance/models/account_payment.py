from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Link the Payment to a Contract
    contract_id = fields.Many2one('finance.contract', string="Finance Contract", readonly=True)
    
    # Optional: Display vehicle info on the payment for easier search
    asset_reg_no = fields.Char(related='contract_id.asset_reg_no', string="Asset Reg", store=True)