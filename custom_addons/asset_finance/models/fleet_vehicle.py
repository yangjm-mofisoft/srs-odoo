from odoo import models, fields

class FleetVehicleExtend(models.Model):
    _inherit = 'fleet.vehicle'

    # Add finance-specific fields to fleet.vehicle
    engine_no = fields.Char(string="Engine No")
    engine_capacity = fields.Char(string="Engine Capacity")
    year_manufacture = fields.Integer(string="Year of Manufacture")
    vehicle_condition = fields.Selection([
        ('new', 'New'),
        ('used', 'Used')
    ], string="Vehicle Condition", default='new')
    
    # Link back to Finance Asset for visibility
    finance_asset_id = fields.Many2one('finance.asset', string="Related Finance Asset", readonly=True)


class FleetVehicleModelBrand(models.Model):
    _inherit = 'fleet.vehicle.model.brand'

    # Add One2many field to access all models for this brand
    model_ids = fields.One2many('fleet.vehicle.model', 'brand_id', string="Models")

    # Additional fields for Make
    country_id = fields.Many2one('res.country', string="Country of Origin")
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    # Additional fields for Model
    engine_capacity = fields.Char(string="Default Engine Capacity",
                                   help="Common engine capacity for this model (e.g., 2.0L, 1800cc)")
    description = fields.Text(string="Description")

    # Note: vehicle_type already exists in fleet.vehicle.model with values: car, bike
    # Note: active already exists in fleet.vehicle.model
