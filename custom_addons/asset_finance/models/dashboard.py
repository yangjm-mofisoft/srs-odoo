from odoo import models, fields, api, tools
import json
from datetime import datetime, timedelta

class FinanceDashboard(models.Model):
    _name = 'finance.dashboard'
    _description = 'Finance Dashboard Analytics'
    _auto = False  # <--- NO REAL TABLE
    
    name = fields.Char(default="Dashboard")

    # --- JSON Data for Charts ---
    # store=False is default, so this is calculated in memory every time you load the page
    chart_data_json = fields.Text(compute='_compute_chart_data')

    # --- KPIs ---
    total_active_contracts = fields.Integer(compute='_compute_kpis')
    total_portfolio_value = fields.Monetary(compute='_compute_kpis', currency_field='currency_id')
    total_overdue = fields.Monetary(compute='_compute_kpis', currency_field='currency_id')
    overdue_percentage = fields.Float(compute='_compute_kpis')
    total_penalties = fields.Monetary(compute='_compute_kpis', currency_field='currency_id')
    
    total_disbursed_mtd = fields.Monetary(compute='_compute_mtd', currency_field='currency_id')
    total_collected_mtd = fields.Monetary(compute='_compute_mtd', currency_field='currency_id')

    # --- Aging ---
    current_amount = fields.Monetary(compute='_compute_aging', currency_field='currency_id')
    overdue_1_30 = fields.Monetary(compute='_compute_aging', currency_field='currency_id')
    overdue_31_60 = fields.Monetary(compute='_compute_aging', currency_field='currency_id')
    overdue_61_90 = fields.Monetary(compute='_compute_aging', currency_field='currency_id')
    overdue_90_plus = fields.Monetary(compute='_compute_aging', currency_field='currency_id')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # --- KEY CHANGE: Initialize the Virtual Record ---
    def init(self):
        """Create a simple SQL view that always returns one record (ID 1)"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT 
                    1 as id, 
                    {self.env.company.currency_id.id} as currency_id,
                    'Dashboard' as name
            )
        """)

    def _compute_chart_data(self):
        """Serialize chart data to JSON"""
        for rec in self:
            # We call the helper method to get the dict
            data = self.get_chart_data()
            rec.chart_data_json = json.dumps(data)

    @api.model
    def get_chart_data(self):
        """Logic to fetch chart numbers"""
        today = fields.Date.today()
        months_data = []

        for i in range(5, -1, -1):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_month - timedelta(days=1)

            disbursed = self.env['account.move'].search([
                ('ref', 'like', 'Disbursement for%'),
                ('date', '>=', month_start), ('date', '<=', month_end),
                ('state', '=', 'posted')
            ])
            
            payments = self.env['account.payment'].search([
                ('contract_id', '!=', False),
                ('payment_type', '=', 'inbound'),
                ('date', '>=', month_start), ('date', '<=', month_end),
                ('state', '=', 'posted')
            ])

            months_data.append({
                'month': month_start.strftime('%b %Y'),
                'disbursed': sum(disbursed.mapped('amount_total')),
                'collected': sum(payments.mapped('amount')),
            })

        return {'monthly_trend': months_data}

    def _compute_kpis(self):
        for rec in self:
            active_contracts = self.env['finance.contract'].search([('ac_status', '=', 'active')])
            rec.total_active_contracts = len(active_contracts)
            rec.total_portfolio_value = sum(active_contracts.mapped('os_balance'))
            rec.total_penalties = sum(active_contracts.mapped('accrued_penalty'))

            total_outstanding = sum(active_contracts.mapped('balance_installment'))
            overdue_contracts = active_contracts.filtered(lambda c: c.total_overdue_days > 0)
            rec.total_overdue = sum(overdue_contracts.mapped('balance_installment'))
            
            if total_outstanding > 0:
                rec.overdue_percentage = (rec.total_overdue / total_outstanding) * 100
            else:
                rec.overdue_percentage = 0.0

    def _compute_mtd(self):
        today = fields.Date.today()
        first_day = today.replace(day=1)
        for rec in self:
            disbursed = self.env['account.move'].search([
                ('ref', 'like', 'Disbursement for%'),
                ('date', '>=', first_day), ('date', '<=', today),
                ('state', '=', 'posted')
            ])
            rec.total_disbursed_mtd = sum(disbursed.mapped('amount_total'))

            payments = self.env['account.payment'].search([
                ('contract_id', '!=', False),
                ('payment_type', '=', 'inbound'),
                ('date', '>=', first_day), ('date', '<=', today),
                ('state', '=', 'posted')
            ])
            rec.total_collected_mtd = sum(payments.mapped('amount'))

    def _compute_aging(self):
        for rec in self:
            active_contracts = self.env['finance.contract'].search([('ac_status', '=', 'active')])
            rec.current_amount = sum(active_contracts.filtered(lambda c: c.total_overdue_days == 0).mapped('balance_installment'))
            rec.overdue_1_30 = sum(active_contracts.filtered(lambda c: 0 < c.total_overdue_days <= 30).mapped('balance_installment'))
            rec.overdue_31_60 = sum(active_contracts.filtered(lambda c: 30 < c.total_overdue_days <= 60).mapped('balance_installment'))
            rec.overdue_61_90 = sum(active_contracts.filtered(lambda c: 60 < c.total_overdue_days <= 90).mapped('balance_installment'))
            rec.overdue_90_plus = sum(active_contracts.filtered(lambda c: c.total_overdue_days > 90).mapped('balance_installment'))

    
    def action_view_active_contracts(self):
        """Open active contracts"""
        return {
            'name': 'Active Contracts',
            'type': 'ir.actions.act_window',
            'res_model': 'finance.contract',
            'view_mode': 'list,form',
            'domain': [('ac_status', '=', 'active')],
            'context': {'search_default_active': 1}
        }

    def action_view_overdue(self):
        """Open overdue contracts"""
        return {
            'name': 'Overdue Contracts',
            'type': 'ir.actions.act_window',
            'res_model': 'finance.contract',
            'view_mode': 'list,form',
            'domain': [('ac_status', '=', 'active'), ('total_overdue_days', '>', 0)],
        }

    def action_view_disbursements(self):
        """Open disbursement journal entries"""
        return {
            'name': 'Disbursements',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('ref', 'like', 'Disbursement for%')],
        }

    def action_view_collections(self):
        """Open payment collections"""
        return {
            'name': 'Collections',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('contract_id', '!=', False), ('payment_type', '=', 'inbound')],
        }
