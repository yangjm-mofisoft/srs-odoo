from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FinanceAsset(models.Model):
    _name = 'finance.asset'
    _description = 'Financed Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    # --- 1. COMMON IDENTIFIERS ---
    name = fields.Char(string="Asset Name", required=True, help="e.g. Toyota Camry 2023")
    internal_ref = fields.Char(string="Internal Asset Code")

    @api.model
    def _get_default_asset_type(self):
        """Fetch default asset type from system settings"""
        key = 'asset_finance.default_asset_type'
        default_value = 'vehicle'
        param = self.env['ir.config_parameter'].sudo().search([('key', '=', key)], limit=1)
        return param.value if param else default_value

    @api.model
    def _get_asset_type_selection(self):
        """Dynamically generate asset type selection based on configuration"""
        key = 'asset_finance.supported_asset_types'
        default_value = 'vehicle'
        param = self.env['ir.config_parameter'].sudo().search([('key', '=', key)], limit=1)
        supported_str = param.value if param else default_value
        supported = [s.strip() for s in supported_str.split(',')]
        all_types = {'vehicle': 'Vehicle', 'equipment': 'Equipment', 'property': 'Property', 'other': 'Other'}
        return [(key, all_types[key]) for key in supported if key in all_types] or [('vehicle', 'Vehicle')]

    asset_type = fields.Selection(
        selection='_get_asset_type_selection',
        string="Asset Type",
        default=_get_default_asset_type,
        required=True,
        help="Type of asset being financed"
    )

    # --- 2. GENERIC FIELDS ---
    serial_no = fields.Char(string="Serial No.", tracking=True)
    description = fields.Text(string="Description / Notes")

    # --- 3. VEHICLE SPECIFIC ---
    # Link to the master Fleet Vehicle record. This is the single source of truth.
    vehicle_id = fields.Many2one('fleet.vehicle', string="Fleet Vehicle Record",
                                 copy=False, help="Auto-managed link to the single source of truth in the Fleet module.")

    # Vehicle fields are now related to the fleet.vehicle model.
    # This makes fleet.vehicle the single source of truth.
    registration_no = fields.Char(related='vehicle_id.license_plate', readonly=False, store=True, string="Registration No / ID", tracking=True)
    chassis_no = fields.Char(related='vehicle_id.vin_sn', readonly=False, store=True, string="Chassis No / VIN", tracking=True)
    
    # Note: The UX for selecting Make/Model changes. User selects a model, and make is auto-filled.
    vehicle_model_id = fields.Many2one(related='vehicle_id.model_id', readonly=False, store=True, string="Model")
    vehicle_make_id = fields.Many2one(related='vehicle_id.model_id.brand_id', readonly=True, store=True, string="Make")

    engine_no = fields.Char(related='vehicle_id.engine_no', readonly=False, store=True, string="Engine No")
    # The 'engine_capacity' and 'year_manufacture' fields do not exist on the standard Odoo 16+ fleet.vehicle model.
    # Kept as local fields. Add to fleet model if needed.
    engine_capacity = fields.Char(string="Engine Capacity")
    year_manufacture = fields.Integer(string="Year of Manufacture")

    vehicle_color = fields.Char(related='vehicle_id.color', readonly=False, store=True, string="Vehicle Color")
    vehicle_condition = fields.Selection(related='vehicle_id.vehicle_condition', readonly=False, store=True, string="Vehicle Condition")

    # This field is specific to the finance workflow, so it remains a local field.
    vehicle_type = fields.Selection([
        ('passenger', 'Passenger'),
        ('commercial', 'Commercial'),
        ('motorcycle', 'Motorcycle'),
        ('bus', 'Bus'),
        ('goods', 'Goods Vehicle')
    ], string="Vehicle Type")
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
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # --- 5. CONTRACT VISIBILITY ---
    contract_ids = fields.One2many('finance.contract', 'asset_id', string="Contracts")
    current_contract_id = fields.Many2one('finance.contract', compute='_compute_current_contract', store=True, string="Active Contract")

    @api.depends('contract_ids.ac_status')
    def _compute_current_contract(self):
        for rec in self:
            active = rec.contract_ids.filtered(lambda c: c.ac_status in ['active', 'repo'])
            rec.current_contract_id = active[0] if active else False

    @api.depends('name', 'registration_no', 'serial_no')
    def _compute_display_name(self):
        for rec in self:
            if rec.registration_no:
                rec.display_name = f"{rec.registration_no} ({rec.name})"
            elif rec.serial_no:
                rec.display_name = f"{rec.serial_no} ({rec.name})"
            else:
                rec.display_name = rec.name

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to auto-create fleet.vehicle for vehicle assets.
        This ensures the vehicle_id exists before related fields are written.
        """
        records = super(FinanceAsset, self).create(vals_list)
        for record in records.filtered(lambda r: r.asset_type == 'vehicle'):
            record._create_fleet_vehicle_if_needed()
        return records

    def write(self, vals):
        """
        Override write to ensure fleet.vehicle exists if asset_type is changed to vehicle.
        """
        res = super(FinanceAsset, self).write(vals)
        if 'asset_type' in vals and vals['asset_type'] == 'vehicle':
            for record in self:
                record._create_fleet_vehicle_if_needed()
        return res

    def _create_fleet_vehicle_if_needed(self):
        """
        Creates a fleet.vehicle record and links it if one doesn't already exist.
        This method is the key to the related fields working correctly.
        """
        self.ensure_one()
        if not self.vehicle_id:
            fleet_vehicle = self.env['fleet.vehicle'].create({
                'name': self.name,
                'finance_asset_id': self.id,
            })
            self.vehicle_id = fleet_vehicle
