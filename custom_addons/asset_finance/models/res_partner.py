from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # --- Identity ---
    nric = fields.Char(string="NRIC / FIN / UEN", help="National ID or Company Reg No")
    date_of_birth = fields.Date(string="Date of Birth / Incorporation")

    # --- Finance Partner Type (Only for Business Entities) ---
    # Note: Customers, Guarantors, Co-Borrowers can be EITHER individuals OR companies
    # This field is ONLY for specialized business entity types
    finance_partner_type = fields.Selection([
        ('broker', 'Sales Agent / Broker'),
        ('insurer', 'Insurance Company'),
        ('finance_company', 'Finance Company'),
        ('supplier', 'Supplier / Dealer'),
    ], string="Finance Business Type",
       tracking=True,
       help="Only for specialized business entities. Leave blank for regular customers/guarantors/co-borrowers (who can be individuals or companies)")

    # --- DEPRECATED: Old Boolean Fields (kept for migration) ---
    # These will be removed after migration is complete
    is_finance_guarantor = fields.Boolean(string="Is Guarantor (Deprecated)", help="DEPRECATED: Use finance_partner_type instead.")
    is_finance_broker = fields.Boolean(string="Is Broker (Deprecated)", help="DEPRECATED: Use finance_partner_type instead.")
    is_finance_joint_hirer = fields.Boolean(string="Is Co-Borrower (Deprecated)", help="DEPRECATED: Use finance_partner_type instead.")

    # --- Risk Management ---
    finance_blacklist = fields.Boolean(string="Blacklisted (Finance)")
    finance_blacklist_reason = fields.Char(string="Blacklist Reason")

    # Odoo has a standard 'type' field (Invoice, Delivery, Other).
    # We add a specific classification for your Finance needs.
    address_category = fields.Selection([
        ('residential', 'Residential'),
        ('work', 'Work / Office'),
        ('registered', 'Registered Address'),
        ('mailing', 'Mailing Address'),
        ('previous', 'Previous Address')
    ], string="Address Category")

    # Multiple Contact Numbers ---
    phone_ids = fields.One2many('res.partner.phone', 'partner_id', string="Contact Numbers")