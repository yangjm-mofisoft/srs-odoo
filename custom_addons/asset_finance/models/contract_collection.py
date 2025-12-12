from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FinanceContract(models.Model):
    _inherit = 'finance.contract'

    # --------------------------------------------------------
    # PENALTY & OVERDUE LOGIC
    # --------------------------------------------------------

    @api.depends('line_ids.date_due', 'line_ids.invoice_id.payment_state')
    def _compute_overdue_status(self):
        """Calculate total overdue days and update late status"""
        today = fields.Date.today()

        # Get grace period from configuration
        param = self.env['ir.config_parameter'].sudo().search([('key', '=', 'asset_finance.grace_period_days')], limit=1)
        grace_period = int(param.value) if param else 7

        for rec in self:
            # Find the oldest unpaid line that is overdue
            overdue_lines = rec.line_ids.filtered(
                lambda l: l.date_due and l.date_due < today and l.invoice_id.payment_state != 'paid'
            )

            if overdue_lines:
                # Get the earliest due date
                earliest_due = min(overdue_lines.mapped('date_due'))
                delta = (today - earliest_due).days

                # Apply grace period
                rec.total_overdue_days = max(0, delta - grace_period)

                # Auto-update Late Status based on days
                if rec.total_overdue_days > 90:
                    rec.late_status = 'legal'
                elif rec.total_overdue_days > 30:
                    rec.late_status = 'attention'
                else:
                    rec.late_status = 'normal'
            else:
                rec.total_overdue_days = 0
                rec.late_status = 'normal'

    # --------------------------------------------------------
    # PENALTY CALCULATION (CRON JOB)
    # --------------------------------------------------------

    def _cron_calculate_late_interest(self):
        """
        Run nightly to calculate penalties based on the selected Rule.
        Called by scheduled action defined in data/cron.xml.

        Optimized with batch commits to prevent long-running transaction locks.
        """
        # Ensure we only check active contracts that have a rule assigned
        active_contracts = self.search([('ac_status', '=', 'active'), ('penalty_rule_id', '!=', False)])
        today = fields.Date.today()

        batch_size = 100  # Process 100 contracts per batch to prevent DB locks
        total_processed = 0
        total_penalties_accrued = 0.0

        for i in range(0, len(active_contracts), batch_size):
            batch = active_contracts[i:i + batch_size]

            # Process each contract in the batch
            for contract in batch:
                try:
                    rule = contract.penalty_rule_id
                    penalty_amount = 0.0

                    # Find overdue lines
                    overdue_lines = contract.line_ids.filtered(
                        lambda l: l.date_due and l.date_due < today and l.invoice_id.payment_state != 'paid'
                    )

                    for line in overdue_lines:
                        days_late = (today - line.date_due).days

                        # Check Grace Period
                        if days_late <= rule.grace_period_days:
                            continue

                        if rule.method == 'daily_percent':
                            # Logic: (Principal * Rate / 100) / 365
                            daily_rate = (rule.rate / 100) / 365
                            daily_penalty = line.amount_principal * daily_rate
                            penalty_amount += daily_penalty

                        elif rule.method == 'fixed_one_time':
                            # Check if penalty was already applied for this line
                            if not line.penalty_applied:
                                penalty_amount += rule.fixed_amount
                                line.penalty_applied = True

                    # Update the balance
                    if penalty_amount > 0:
                        contract.accrued_penalty += penalty_amount
                        contract.balance_late_charges = contract.accrued_penalty - contract.total_late_paid

                        # Log in chatter
                        contract.message_post(
                            body=f"Penalty of {contract.currency_id.symbol}{penalty_amount:.2f} accrued. "
                                 f"Total penalties: {contract.currency_id.symbol}{contract.accrued_penalty:.2f}"
                        )

                        total_penalties_accrued += penalty_amount
                        total_processed += 1

                except Exception as e:
                    # Log error but continue processing other contracts
                    contract.message_post(
                        body=f"Error calculating penalty: {str(e)}",
                        message_type='notification'
                    )
                    continue

            # Commit after each batch to prevent long-running locks
            self.env.cr.commit()

        # Log summary in server logs
        if total_processed > 0:
            _logger = self.env['ir.logging']
            _logger.sudo().create({
                'name': 'Penalty Calculation Cron',
                'type': 'server',
                'level': 'info',
                'message': f"Processed {total_processed} contracts. Total penalties accrued: {total_penalties_accrued:.2f}",
                'path': 'asset_finance.contract_collection',
                'func': '_cron_calculate_late_interest',
                'line': '49'
            })

    # --------------------------------------------------------
    # COLLECTION NOTICES & ACTIONS
    # --------------------------------------------------------

    def action_send_reminder(self):
        """Send payment reminder email"""
        self.ensure_one()
        if not self.hirer_id.email:
            raise UserError(_("Hirer email address is missing. Please update the partner record."))

        template = self.env.ref('asset_finance.email_template_payment_reminder', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

        self.date_reminder_sent = fields.Date.today()
        self.message_post(body="Payment Reminder Email sent to Hirer.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Payment reminder sent successfully.'),
                'type': 'success'
            }
        }

    def action_send_overdue_notice(self):
        """Send overdue notice email"""
        self.ensure_one()
        if not self.hirer_id.email:
            raise UserError(_("Hirer email address is missing. Please update the partner record."))

        template = self.env.ref('asset_finance.email_template_overdue_notice', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

        self.message_post(body="Overdue Notice sent via email.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Overdue notice sent successfully.'),
                'type': 'warning'
            }
        }

    def action_send_4th_schedule(self):
        """Send 4th Schedule notice (Legal demand for payment)"""
        self.ensure_one()
        if not self.hirer_id.email:
            raise UserError(_("Hirer email address is missing. Please update the partner record."))

        template = self.env.ref('asset_finance.email_template_4th_schedule', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

        self.date_4th_sched_sent = fields.Date.today()
        self.message_post(body="4th Schedule Notice sent via email.")

        # Update status to Legal if not already
        if self.late_status != 'legal':
            self.late_status = 'legal'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Warning'),
                'message': _('4th Schedule notice sent. Contract status updated to Legal Action.'),
                'type': 'warning'
            }
        }

    def action_issue_repo_order(self):
        """Issue repossession order"""
        self.ensure_one()

        # Confirm action
        self.date_repo_order = fields.Date.today()
        self.ac_status = 'repo'
        self.asset_id.status = 'repo'

        self.message_post(
            body="⚠️ Repossession Order Issued. Contract status updated to Repossessed."
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Repossession Order Issued'),
                'message': _('Contract and asset marked as repossessed.'),
                'type': 'danger',
                'sticky': True
            }
        }

    def action_send_5th_schedule(self):
        """Send 5th Schedule notice (Post-repossession notice)"""
        self.ensure_one()
        self.date_5th_sched_sent = fields.Date.today()
        self.message_post(body="5th Schedule Notice Issued (Post-Repossession).")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Notice Sent'),
                'message': _('5th Schedule notice issued.'),
                'type': 'info'
            }
        }

    def action_send_settlement_quotation(self):
        """Send settlement quotation email"""
        self.ensure_one()
        if not self.hirer_id.email:
            raise UserError(_("Hirer email address is missing. Please update the partner record."))

        template = self.env.ref('asset_finance.email_template_settlement_quotation', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

        self.message_post(body="Settlement Quotation sent via email.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Settlement quotation sent successfully.'),
                'type': 'success'
            }
        }

    # --------------------------------------------------------
    # BATCH COLLECTION ACTIONS
    # --------------------------------------------------------

    def action_batch_send_reminders(self):
        """Send payment reminders to all selected contracts"""
        success_count = 0
        error_count = 0

        for contract in self:
            try:
                if contract.hirer_id.email:
                    contract.action_send_reminder()
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                contract.message_post(body=f"Failed to send reminder: {str(e)}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Batch Reminder Complete'),
                'message': _(f'Sent: {success_count}, Failed: {error_count}'),
                'type': 'success' if error_count == 0 else 'warning'
            }
        }
