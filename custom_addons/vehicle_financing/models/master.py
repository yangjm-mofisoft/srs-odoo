from odoo import models, fields

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