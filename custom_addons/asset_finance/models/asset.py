from odoo import models, fields, api

class FinanceAsset(models.Model):
    _name = 'finance.asset'
    _description = 'Financed Asset'
    _rec_name = 'display_name'

    name = fields.Char(string="Asset Name", required=True, help="A descriptive name for the asset, e.g., 'Toyota Camry 2023'.")
    asset_type = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment'),
        ('property', 'Property'),
        ('other', 'Other')
    ], string="Asset Type", required=True, default='vehicle')
    
    # Link to standard Odoo Fleet module
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle Record", 
                                 help="Link to a vehicle record in the Fleet module for detailed vehicle specs.")

    # General Asset Information
    serial_no = fields.Char(string="Serial / Chassis No.")
    internal_ref = fields.Char(string="Internal Reference")
    description = fields.Text(string="Description")
    
    status = fields.Selection([
        ('available', 'Available'),
        ('financed', 'Financed'),
        ('maintenance', 'Maintenance'),
        ('sold', 'Sold'),
        ('writeoff', 'Written-off')
    ], string="Asset Status", default='available', tracking=True)

    # Computed field for easy identification
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)

    @api.depends('name', 'vehicle_id.license_plate', 'serial_no')
    def _compute_display_name(self):
        for rec in self:
            if rec.asset_type == 'vehicle' and rec.vehicle_id and rec.vehicle_id.license_plate:
                rec.display_name = f"{rec.vehicle_id.license_plate} ({rec.name})"
            elif rec.serial_no:
                rec.display_name = f"{rec.name} ({rec.serial_no})"
            else:
                rec.display_name = rec.name