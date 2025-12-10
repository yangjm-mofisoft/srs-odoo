from odoo import models, fields

class FinanceAsset(models.Model):
    _inherit = 'finance.asset'

    # --- SG Classification (OPC/PHV/OMV) ---
    opc = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="OPC (Off Peak Car)")
    phv = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="PHV (Private Hire)")
    omv_check = fields.Selection([('above', 'Above'), ('below', 'Below')], string="OMV Check")

    # --- SG Financials (COE/ARF/PARF) ---
    coe_no = fields.Char(string="COE No")
    coe_amount = fields.Monetary(string="COE Amount", currency_field='currency_id')
    coe_category = fields.Selection([
        ('A', 'Cat A'), ('B', 'Cat B'), ('C', 'Cat C'), ('E', 'Cat E')
    ], string="COE Category")
    
    arf_amount = fields.Monetary(string="ARF Amount")
    parf_amount = fields.Monetary(string="PARF Amount")
    parf_expire_date = fields.Date(string="PARF Expire Date")
    
    market_valuation = fields.Monetary(string="Market Valuation")