# Finance Dashboard - User Guide

## Overview

The Finance Dashboard provides real-time insights into your portfolio performance, collections status, and key financial metrics. It's designed to give managers and staff a quick overview of the business health at a glance.

---

## Accessing the Dashboard

1. Navigate to **Asset Finance** → **Dashboard**
2. The dashboard is the first menu item for quick access
3. All users with Finance Officer, Manager, or Collection Staff roles can view it

---

## Dashboard Components

### 1. **KPI Cards (Top Row)**

#### Active Contracts
- **Shows**: Total number of active contracts
- **Color**: Blue
- **Icon**: File
- **Use Case**: Quick count of current portfolio size

#### Portfolio Value
- **Shows**: Total outstanding balance across all active contracts
- **Color**: Green
- **Icon**: Briefcase
- **Format**: Displayed in thousands (e.g., "250K")
- **Use Case**: Total capital deployed

#### Total Overdue
- **Shows**: Sum of overdue balances
- **Percentage**: Overdue as % of total portfolio
- **Color**: Orange/Warning
- **Icon**: Exclamation triangle
- **Use Case**: Collection focus metric

#### Penalties
- **Shows**: Total accrued penalties
- **Color**: Red
- **Icon**: Gavel
- **Format**: In thousands
- **Use Case**: Revenue from late charges

---

### 2. **Month-to-Date (MTD) Summary**

#### Disbursed (MTD)
- Displays total loan amounts disbursed this month
- Tracks new business volume
- Updated in real-time

#### Collected (MTD)
- Shows total payments received this month
- Tracks cash flow
- Includes all contract payments

---

### 3. **Aging Analysis**

Visual breakdown of outstanding amounts by aging bucket:

| Bucket | Description | Color | Risk Level |
|--------|-------------|-------|------------|
| **Current** | Not overdue | Green | Low |
| **1-30 Days** | Just overdue | Blue | Low |
| **31-60 Days** | Attention needed | Yellow | Medium |
| **61-90 Days** | Collection focus | Orange | High |
| **90+ Days** | Legal action | Red | Critical |

**Use Cases:**
- Collection prioritization
- Risk assessment
- Credit policy evaluation

---

### 4. **Quick Actions**

Four action buttons for common tasks:

#### Active Contracts
- Opens filtered list of all active contracts
- Quick access to working portfolio
- Click to manage contracts

#### Overdue Accounts
- Shows only overdue contracts
- Sorted by days overdue
- For collections team

#### Disbursements
- Lists all disbursement journal entries
- Track funding activity
- Review disbursement history

#### Collections
- View all payment receipts
- Track collection efficiency
- Payment history

---

## How the Dashboard Works

### Data Computation

The dashboard uses real-time calculations:

```
Portfolio Value = Sum of outstanding balances (active contracts)
Overdue Amount = Sum of balances where overdue_days > 0
Overdue % = (Overdue Amount / Total Outstanding) * 100
Penalties = Sum of accrued penalties across contracts
```

### Refresh Frequency

- **Automatic**: Dashboard refreshes when you navigate to it
- **Manual**: Click browser refresh to update
- **Real-time**: All calculations are live, not cached

### Performance

- Optimized queries for large portfolios
- Handles 1000+ contracts efficiently
- Uses Odoo's ORM for reliability

---

## Interpreting the Metrics

### Healthy Portfolio Indicators

✅ **Good Signs:**
- Overdue % < 5%
- Most balance in "Current" bucket
- MTD Collections > MTD Disbursements
- Low penalty accrual

⚠️ **Warning Signs:**
- Overdue % > 10%
- Growing 90+ days bucket
- Collections < Disbursements for multiple months
- Rising penalty amounts

🚨 **Critical Signs:**
- Overdue % > 20%
- Majority in 90+ days
- Penalties accumulating rapidly
- Multiple contracts in legal status

---

## Use Cases by Role

### Finance Manager

**Daily Tasks:**
1. Check dashboard first thing in morning
2. Review overdue percentage trend
3. Check MTD disbursements vs targets
4. Monitor aging buckets for deterioration
5. Click "Overdue Accounts" for collection priorities

**Weekly Tasks:**
- Compare MTD metrics week-over-week
- Review penalty trends
- Assess portfolio quality

### Finance Officer

**Daily Tasks:**
1. Check active contracts count
2. Monitor new disbursements
3. Track collections received

### Collection Staff

**Daily Tasks:**
1. Focus on aging analysis
2. Use "Overdue Accounts" button
3. Monitor penalty accrual
4. Prioritize 60+ days bucket

---

## Future Enhancements (Roadmap)

### Phase 1 (Planned)
- [ ] Monthly trend charts (Line chart showing 6-month trend)
- [ ] Product type breakdown (Pie chart)
- [ ] Top 10 overdue contracts table
- [ ] Recent activities feed

### Phase 2 (Under Consideration)
- [ ] Comparison with previous month
- [ ] Drill-down by product type
- [ ] Export dashboard to PDF
- [ ] Email scheduled dashboard reports
- [ ] Custom date range selection

### Phase 3 (Future)
- [ ] Predictive analytics (Expected collections)
- [ ] Risk scoring per contract
- [ ] Automated alerts for thresholds
- [ ] Mobile-responsive dashboard

---

## Troubleshooting

### Dashboard Shows Zero Values

**Possible Causes:**
1. No active contracts in system
2. User doesn't have access rights
3. Database not updated after contract changes

**Solutions:**
1. Create test contracts
2. Check security group assignment
3. Refresh browser

### Slow Dashboard Loading

**Possible Causes:**
1. Large number of contracts (1000+)
2. Many installment lines
3. Server performance

**Solutions:**
1. Dashboard is optimized, should be fast
2. Contact system administrator
3. Consider database indexing

### Wrong Numbers Displayed

**Possible Causes:**
1. Browser cache
2. Transactions not posted
3. Contract status not updated

**Solutions:**
1. Hard refresh (Ctrl+F5)
2. Ensure invoices/payments are posted
3. Verify contract ac_status field

---

## Technical Details

### Models Used

| Model | Purpose |
|-------|---------|
| `finance.dashboard` | Main dashboard model |
| `finance.contract` | Contract data source |
| `account.payment` | Collections data |
| `account.move` | Disbursement tracking |
| `finance.contract.line` | Installment details |

### Key Methods

```python
get_dashboard_data()  # Computes all KPIs
get_chart_data()      # Prepares chart datasets
action_view_*()       # Quick action methods
```

### View Type

- **Kanban View**: Bootstrap 4 cards layout
- **No Create/Edit/Delete**: Read-only dashboard
- **Responsive**: Works on tablet and desktop

---

## Best Practices

### For Managers

1. **Review Daily**: Make dashboard your home page
2. **Set Thresholds**: Define acceptable overdue %
3. **Trend Analysis**: Watch week-over-week changes
4. **Action Items**: Create follow-ups from overdue list

### For Collections

1. **Focus Aging**: Prioritize 60-90 days bucket
2. **Track Progress**: Monitor overdue reduction
3. **Use Filters**: Leverage quick actions
4. **Document**: Log collection activities

### For Finance Officers

1. **Quality Control**: Check disbursement accuracy
2. **Reconciliation**: Match collections to invoices
3. **Data Entry**: Ensure timely posting
4. **Support**: Help collections team

---

## Security & Access

### Who Can See What?

| Role | Dashboard Access | Edit Rights |
|------|-----------------|-------------|
| Finance Officer | ✅ View | ❌ Read-only |
| Finance Manager | ✅ View | ❌ Read-only |
| Collection Staff | ✅ View | ❌ Read-only |
| Others | ❌ No Access | ❌ None |

**Note**: Dashboard is read-only for all users. Actions open respective forms with appropriate permissions.

---

## FAQ

**Q: Can I customize the KPIs shown?**
A: Currently no, but this is planned for future versions. Contact your developer for customization.

**Q: Can I export dashboard data?**
A: Not directly, but you can click quick actions to access lists which can be exported.

**Q: How often should I check the dashboard?**
A: Managers: Daily. Officers: 2-3 times daily. Collections: Multiple times daily.

**Q: Can I see historical dashboard data?**
A: Not yet - dashboard shows current state. Historical trends coming in future update.

**Q: Does the dashboard work on mobile?**
A: It works but is optimized for tablet/desktop. Mobile version planned.

---

## Support

For issues or feature requests:
1. Check this guide first
2. Contact your system administrator
3. Log a ticket with IT support
4. Email: support@mofisoft.com

---

**Version**: 1.0
**Last Updated**: 2025-12-10
**Module**: Asset Financing Management v1.1.0
