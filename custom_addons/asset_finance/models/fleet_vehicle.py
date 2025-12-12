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
