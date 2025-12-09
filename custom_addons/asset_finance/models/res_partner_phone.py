from odoo import models, fields, api

class ResPartnerPhone(models.Model):
    _name = 'res.partner.phone'
    _description = 'Detailed Contact Number'

    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    
    # 1. The Number
    name = fields.Char(string="Number", required=True)
    
    # 2. The Type
    contact_type = fields.Selection([
        ('mobile', 'Mobile'),
        ('work', 'Work Phone'),
        ('home', 'Home Phone'),
        ('fax', 'Fax'),
        ('emergency', 'Emergency Contact')
    ], string="Type", default='mobile', required=True)
    
    # 3. Link to an Address (The requirement)
    # We only want to show addresses that belong to THIS partner
    address_id = fields.Many2one(
        'res.partner', 
        string="Linked Address",
        domain="[('parent_id', '=', partner_id), ('type', '!=', 'contact')]",
        help="Link this number to one of the partner's specific addresses (e.g. Work Phone -> Work Address)"
    )
    
    # Optional: Verification
    is_verified = fields.Boolean(string="Verified")