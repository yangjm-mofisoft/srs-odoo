from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # --- Leasing Roles ---
    is_leasing_guarantor = fields.Boolean(string="Is Guarantor", help="Can be selected as a Guarantor.")
    is_leasing_broker = fields.Boolean(string="Is Broker", help="Can be selected as a Broker/Agent.")
    # Co-Borrower Flag
    is_leasing_joint_hirer = fields.Boolean(string="Is Co-Borrower", help="Can be selected as a Joint Hirer/Co-Borrower.")

    # --- Risk Management ---
    leasing_blacklist = fields.Boolean(string="Blacklisted (Leasing)")
    leasing_blacklist_reason = fields.Char(string="Blacklist Reason")