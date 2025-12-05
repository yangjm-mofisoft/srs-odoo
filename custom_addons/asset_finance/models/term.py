from odoo import models, fields, api

class FinanceTerm(models.Model):
    _name = 'finance.term'
    _description = 'Financing Term (Months)'
    _order = 'months'

    name = fields.Char(compute='_compute_name', store=True)
    months = fields.Integer(string="Months", required=True, index=True)

    _sql_constraints = [
        ('months_unique', 'unique(months)', 'Term in months must be unique.')
    ]

    @api.depends('months')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.months} Months"