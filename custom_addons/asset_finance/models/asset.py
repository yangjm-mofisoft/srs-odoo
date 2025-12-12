from odoo import models, fields, api
from odoo.exceptions import ValidationError

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

    # Smart Fields - All readonly, computed from vehicle_id
    registration_no = fields.Char(string="Registration No / ID", compute='_compute_details', store=True, readonly=True, tracking=True)
    chassis_no = fields.Char(string="Chassis No", compute='_compute_details', store=True, readonly=True)
    make = fields.Char(string="Make", compute='_compute_details', store=True, readonly=True)
    model = fields.Char(string="Model", compute='_compute_details', store=True, readonly=True)

    # Generic Vehicle Details - All readonly, computed from vehicle_id
    engine_no = fields.Char(string="Engine No", compute='_compute_details', store=True, readonly=True)
    engine_capacity = fields.Char(string="Engine Capacity", compute='_compute_details', store=True, readonly=True)
    vehicle_type = fields.Selection([
        ('passenger', 'Passenger'),
        ('commercial', 'Commercial'),
        ('motorcycle', 'Motorcycle'),
        ('bus', 'Bus'),
        ('goods', 'Goods Vehicle')
    ], string="Vehicle Type")
    year_manufacture = fields.Integer(string="Year of Manufacture", compute='_compute_details', store=True, readonly=True)
    vehicle_color = fields.Char(string="Vehicle Color", compute='_compute_details', store=True, readonly=True)
    vehicle_condition = fields.Selection([('new', 'New'), ('used', 'Used')], string="Vehicle Condition",
                                         compute='_compute_details', store=True, readonly=True)
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

    @api.depends('asset_type', 'vehicle_id', 'vehicle_id.license_plate', 'vehicle_id.vin_sn', 'vehicle_id.model_id',
                 'vehicle_id.engine_no', 'vehicle_id.engine_capacity', 'vehicle_id.year_manufacture',
                 'vehicle_id.vehicle_condition', 'vehicle_id.color')
    def _compute_details(self):
        for rec in self:
            if rec.asset_type == 'vehicle' and rec.vehicle_id:
                rec.registration_no = rec.vehicle_id.license_plate
                rec.chassis_no = rec.vehicle_id.vin_sn
                rec.make = rec.vehicle_id.model_id.brand_id.name if rec.vehicle_id.model_id else False
                rec.model = rec.vehicle_id.model_id.name if rec.vehicle_id.model_id else False
                rec.serial_no = rec.vehicle_id.vin_sn
                # Sync additional fields from fleet.vehicle
                rec.engine_no = rec.vehicle_id.engine_no
                rec.engine_capacity = rec.vehicle_id.engine_capacity
                rec.year_manufacture = rec.vehicle_id.year_manufacture
                rec.vehicle_condition = rec.vehicle_id.vehicle_condition
                rec.vehicle_color = rec.vehicle_id.color
            else:
                # For non-vehicle assets, clear vehicle-specific fields
                rec.registration_no = False
                rec.chassis_no = False
                rec.make = False
                rec.model = False
                rec.engine_no = False
                rec.engine_capacity = False
                rec.year_manufacture = False
                rec.vehicle_condition = False
                rec.vehicle_color = False

    @api.depends('name', 'registration_no', 'serial_no')
    def _compute_display_name(self):
        for rec in self:
            if rec.registration_no:
                rec.display_name = f"{rec.registration_no} ({rec.name})"
            elif rec.serial_no:
                rec.display_name = f"{rec.serial_no} ({rec.name})"
            else:
                rec.display_name = rec.name

    @api.constrains('asset_type', 'vehicle_id')
    def _check_vehicle_required(self):
        """Ensure vehicle assets must have a linked fleet vehicle"""
        for rec in self:
            if rec.asset_type == 'vehicle' and not rec.vehicle_id:
                raise ValidationError(
                    "Vehicle Record is required for vehicle-type assets. "
                    "Please create or link a fleet vehicle record."
                )