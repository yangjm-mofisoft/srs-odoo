from odoo import models, fields, api

class VehicleAsset(models.Model):
    _name = 'leasing.vehicle'
    _description = 'Vehicle Asset'
    _rec_name = 'reg_no'

    internal_asset_code = fields.Char(string="Internal Asset Code", help="Internal reference/inventory number")
    make = fields.Char(string="Make", required=True)
    model = fields.Char(string="Model", required=True)
    reg_no = fields.Char(string="Registration No.", required=True)
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
        ('sold', 'Sold'),
        ('writeoff', 'Written-off')
    ], string="Asset Status", default='available')

    # ADDED SQL Constraint for Uniqueness
    _sql_constraints = [
        ('reg_no_unique', 'unique(reg_no)', 'Registration No. must be unique!')
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.reg_no} - {record.make} {record.model}"
            result.append((record.id, name))
        return result