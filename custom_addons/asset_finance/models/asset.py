from odoo import models, fields, api

class FinanceAsset(models.Model):
    _name = 'finance.asset'
    _description = 'Financed Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Added tracking
    _rec_name = 'display_name'

    # --- 1. COMMON IDENTIFIERS ---
    name = fields.Char(string="Asset Name", required=True, help="e.g. Toyota Camry 2023")
    internal_ref = fields.Char(string="Internal Asset Code")
    
    asset_type = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment'),
        ('property', 'Property'),
        ('other', 'Other')
    ], string="Asset Type", required=True, default='vehicle')

    # --- 2. GENERIC FIELDS ---
    serial_no = fields.Char(string="Serial No.", tracking=True)
    description = fields.Text(string="Description / Notes")
    
    # --- 3. VEHICLE SPECIFIC (Smart Link Polymorphism Strategy) ---
    # For Vehicles: We link to Odoo's standard Fleet module
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle Record", 
                                 help="Link to a vehicle record in the Fleet module for detailed vehicle specs.")

    # For Others: We might link to Account Asset or Product (Optional)
    # product_id = fields.Many2one('product.product', string="Equipment Product")

    # Smart Fields
    registration_no = fields.Char(string="Registration No / ID", compute='_compute_details', store=True, readonly=False, tracking=True)
    chassis_no = fields.Char(string="Chassis No", compute='_compute_details', store=True, readonly=False)
    make = fields.Char(string="Make", compute='_compute_details', store=True, readonly=False)
    model = fields.Char(string="Model", compute='_compute_details', store=True, readonly=False)
    
    # Generic Vehicle Details
    engine_no = fields.Char(string="Engine No")
    engine_capacity = fields.Char(string="Engine Capacity")
    vehicle_type = fields.Selection([
        ('passenger', 'Passenger'),
        ('commercial', 'Commercial'),
        ('motorcycle', 'Motorcycle'),
        ('bus', 'Bus'),
        ('goods', 'Goods Vehicle')
    ], string="Vehicle Type")
    year_manufacture = fields.Integer(string="Year of Manufacture")
    vehicle_color = fields.Char(string="Vehicle Color")
    vehicle_condition = fields.Selection([('new', 'New'), ('used', 'Used')], string="Vehicle Condition")
    no_of_transfers = fields.Integer(string="Number of Transfers")
    
    # --- 4. STATUS & SYSTEM ---
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    status = fields.Selection([
        ('available', 'Available'),
        ('financed', 'Financed'),
        ('repo', 'Repossessed'),
        ('sold', 'Sold'),
        ('writeoff', 'Written-off')
    ], string="Status", default='available', tracking=True)
    # Computed field for easy identification
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('asset_type', 'vehicle_id', 'vehicle_id.license_plate', 'vehicle_id.vin_sn', 'vehicle_id.model_id')
    def _compute_details(self):
        for rec in self:
            if rec.asset_type == 'vehicle' and rec.vehicle_id:
                rec.registration_no = rec.vehicle_id.license_plate
                rec.chassis_no = rec.vehicle_id.vin_sn
                rec.make = rec.vehicle_id.model_id.brand_id.name
                rec.model = rec.vehicle_id.model_id.name
                rec.serial_no = rec.vehicle_id.vin_sn 
            else:
                rec.registration_no = rec.registration_no
                rec.chassis_no = rec.chassis_no
                rec.make = rec.make
                rec.model = rec.model
                rec.serial_no = rec.serial_no

    @api.depends('name', 'registration_no', 'serial_no')
    def _compute_display_name(self):
        for rec in self:
            if rec.registration_no:
                rec.display_name = f"{rec.registration_no} ({rec.name})"
            elif rec.serial_no:
                rec.display_name = f"{rec.serial_no} ({rec.name})"
            else:
                rec.display_name = rec.name