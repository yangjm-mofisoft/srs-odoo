from odoo import models, fields, api

class VehicleAsset(models.Model):
    _name = 'leasing.vehicle'
    _description = 'Vehicle Asset'
    _rec_name = 'reg_no'

    make = fields.Char(string="Make", required=True)
    model = fields.Char(string="Model", required=True)
    reg_no = fields.Char(string="Registration No.", required=True, unique=True)
    engine_no = fields.Char(string="Engine No.")
    chassis_no = fields.Char(string="Chassis No.")
    year = fields.Integer(string="Year of Manufacture")
    color = fields.Char(string="Color")
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
    ], string="Fuel Type")
    status = fields.Selection([
        ('available', 'Available'),
        ('leased', 'Leased'),
        ('maintenance', 'Maintenance'),
        ('sold', 'Sold')
    ], string="Asset Status", default='available')

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.reg_no} - {record.make} {record.model}"
            result.append((record.id, name))
        return result