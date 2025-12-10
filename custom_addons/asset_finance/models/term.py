from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FinanceTerm(models.Model):
    _name = 'finance.term'
    _description = 'Financing Term (Months)'
    _order = 'months'

    name = fields.Char(compute='_compute_name', store=True)
    months = fields.Integer(string="Months", required=True, index=True)

    # --- Python Constraint (Safe & Works in all versions) ---
    @api.constrains('months')
    def _check_months_unique(self):
        for rec in self:
            if self.search_count([('months', '=', rec.months), ('id', '!=', rec.id)]) > 0:
                raise ValidationError("Term in months must be unique.")

    @api.depends('months')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.months} Months"