# Testing Accounts Setup Guide - Asset Finance Module

## Overview
This guide provides step-by-step instructions for setting up testing accounts with different security roles to test the Asset Financing module functionality.

---

## Table of Contents
1. [Security Groups Overview](#security-groups-overview)
2. [Initial Setup](#initial-setup)
3. [Creating Test Users](#creating-test-users)
4. [Testing Scenarios by Role](#testing-scenarios-by-role)
5. [Sample Test Data](#sample-test-data)
6. [Troubleshooting](#troubleshooting)

---

## Security Groups Overview

The Asset Finance module defines **3 security groups**:

| Group | Internal Name | Access Level | Key Permissions |
|-------|--------------|--------------|-----------------|
| **Finance Officer** | `group_finance_officer` | Create & Manage | ✅ Create contracts<br>✅ Edit draft/active contracts<br>✅ View all contracts<br>❌ Cannot approve<br>❌ Cannot disburse<br>❌ Cannot delete |
| **Finance Manager** | `group_finance_manager` | Full Access | ✅ All Officer permissions<br>✅ Approve contracts<br>✅ Disburse funds<br>✅ Close contracts<br>✅ Delete records<br>✅ Configure settings |
| **Collection Staff** | `group_collection_staff` | Read & Collect | ✅ View active/repo contracts<br>✅ Send collection notices<br>✅ Update penalties<br>❌ Cannot create contracts<br>❌ Cannot approve<br>❌ Cannot disburse |

---

## Initial Setup

### Prerequisites
Before creating test users, ensure:

1. **Module Installed**
   - Navigate to: **Apps**
   - Search: "Asset Financing Management"
   - Ensure status is: **Installed**

2. **Activate Developer Mode**
   - Navigate to: **Settings**
   - Scroll to bottom → Click **Activate the developer mode**
   - Or use URL: `http://your-domain/web?debug=1`

3. **Configure Base Accounting** (Required)
   - Navigate to: **Asset Finance → Configuration → Chart of Accounts**
   - Ensure basic accounts exist:
     - Assets → Current Assets → Receivables
     - Assets → Current Assets → Bank
     - Liabilities → Current Liabilities → Unearned Revenue
     - Income → Operating Income → Interest Income

---

## Creating Test Users

### Step 1: Access User Management
1. Navigate to: **Settings → Users & Companies → Users**
2. Click: **Create** button

### Step 2: Create Finance Officer Account

**Basic Information:**
```
Name: Test Finance Officer
Email: finance.officer@test.com
```

**Access Rights (Settings tab):**
1. Scroll to **Other** section
2. Find **Asset Financing** group
3. Select: **Finance Officer**

**Additional Recommended Groups:**
- ✅ Accounting: Billing
- ✅ Sales: User (for customer management)

**Login Credentials:**
- Set a simple password: `test123` (testing only!)

**Click: Save**

---

### Step 3: Create Finance Manager Account

**Basic Information:**
```
Name: Test Finance Manager
Email: finance.manager@test.com
```

**Access Rights (Settings tab):**
1. Scroll to **Other** section
2. Find **Asset Financing** group
3. Select: **Finance Manager**

**Additional Recommended Groups:**
- ✅ Accounting: Accountant
- ✅ Sales: User
- ✅ Administration: Settings (for configuration access)

**Login Credentials:**
- Set a simple password: `manager123` (testing only!)

**Click: Save**

---

### Step 4: Create Collection Staff Account

**Basic Information:**
```
Name: Test Collection Staff
Email: collection.staff@test.com
```

**Access Rights (Settings tab):**
1. Scroll to **Other** section
2. Find **Asset Financing** group
3. Select: **Collection Staff**

**Additional Recommended Groups:**
- ✅ (No additional groups needed)

**Login Credentials:**
- Set a simple password: `collect123` (testing only!)

**Click: Save**

---

### Step 5: Verify User Creation

**Test Login for Each User:**
1. Logout from admin account
2. Login with each test account
3. Verify **Asset Finance** menu is visible
4. Verify appropriate menu items based on role

**Quick Verification:**
```
Admin Account → Settings → Users → Users
- Should see 4 users total (admin + 3 test users)
- Each should have appropriate group badge
```

---

## Testing Scenarios by Role

### Test Scenario 1: Finance Officer Workflow

**Login As:** `finance.officer@test.com` / `test123`

#### Test 1.1: Create New Contract ✅
1. Navigate to: **Asset Finance → Operations → Contracts**
2. Click: **Create**
3. Fill in contract details:
   ```
   Agreement No: Will auto-generate
   Product: Select "Hire Purchase 5-Year"
   Asset: Select existing or create new vehicle
   Hirer: Select existing customer or create new
   Cash Price: 50,000
   Down Payment: 10,000
   Interest Rate: 8.5%
   Number of Installments: 60 Months
   ```
4. Click: **Save**
5. **Expected Result:** Contract created in **Draft** status

#### Test 1.2: Generate Schedule ✅
1. Open the created contract
2. Click: **Generate Schedule** button
3. **Expected Result:** Installment schedule appears in **Installments** tab

#### Test 1.3: Attempt to Approve ❌ (Should Fail)
1. Open the draft contract
2. **Expected Result:** **Approve** button should be **invisible** or **disabled**
3. Verify message: Only Finance Managers can approve

#### Test 1.4: Attempt to Disburse ❌ (Should Fail)
1. Open an active contract (have admin create one)
2. **Expected Result:** **Disburse** button should be **invisible**

#### Test 1.5: Edit Existing Contract ✅
1. Navigate to existing draft contract
2. Modify down payment amount
3. Click: **Save**
4. **Expected Result:** Changes saved successfully

#### Test 1.6: Attempt to Delete ❌ (Should Fail)
1. Open any contract
2. Click: **Action → Delete**
3. **Expected Result:** Access error message

---

### Test Scenario 2: Finance Manager Workflow

**Login As:** `finance.manager@test.com` / `manager123`

#### Test 2.1: Approve Contract ✅
1. Navigate to: **Asset Finance → Operations → Contracts**
2. Open a **Draft** contract
3. Click: **Approve** button
4. **Expected Result:**
   - Status changes to **Active**
   - Chatter log shows approval

#### Test 2.2: Disburse Funds ✅
1. Open an **Active** contract (not yet disbursed)
2. Click: **Disburse** button
3. Fill wizard:
   ```
   Disbursement Date: Today
   Payment Method: Bank
   Bank Account: Select bank account
   ```
4. Click: **Confirm Disbursement**
5. **Expected Result:**
   - Journal entry created
   - Contract status remains **Active**
   - Disbursement entry visible via button

#### Test 2.3: Create Invoices ✅
1. Set a contract's first due date to past date
2. Click: **Create Invoices** button
3. **Expected Result:** Customer invoices generated for due installments

#### Test 2.4: Process Early Settlement ✅
1. Open an active contract with payments made
2. Click: **Early Settlement** button
3. Review settlement calculation:
   - Outstanding Principal
   - Unearned Interest
   - Rebate Amount
   - Total Settlement Amount
4. Click: **Process Settlement**
5. Fill payment details and confirm
6. **Expected Result:**
   - Contract status → **Closed**
   - Journal entry created
   - Remaining invoices cancelled

#### Test 2.5: Configure Module Settings ✅
1. Navigate to: **Asset Finance → Configuration → Settings**
2. Modify settings:
   ```
   HP Act Limit: $60,000
   Grace Period: 10 days
   Settlement Rebate Fee: 25%
   ```
3. Click: **Save**
4. **Expected Result:** Settings saved successfully

#### Test 2.6: Delete Contract ✅
1. Open a **Draft** contract (no disbursements)
2. Click: **Action → Delete**
3. Confirm deletion
4. **Expected Result:** Contract deleted

---

### Test Scenario 3: Collection Staff Workflow

**Login As:** `collection.staff@test.com` / `collect123`

#### Test 3.1: View Active Contracts ✅
1. Navigate to: **Asset Finance → Operations → Contracts**
2. **Expected Result:**
   - Only **Active** and **Repossessed** contracts visible
   - Draft and Closed contracts NOT visible

#### Test 3.2: View Dashboard ✅
1. Navigate to: **Asset Finance → Dashboard**
2. **Expected Result:**
   - KPIs displayed
   - Aging buckets visible
   - Quick action buttons work

#### Test 3.3: Send Payment Reminder ✅
1. Open an **Active** contract
2. Click: **Send Reminder** button
3. **Expected Result:**
   - Email sent to hirer
   - Chatter log updated
   - Date recorded in contract

#### Test 3.4: Send Overdue Notice ✅
1. Open an overdue contract
2. Click: **Send Overdue Notice** button
3. **Expected Result:**
   - Email sent
   - Chatter updated

#### Test 3.5: Send 4th Schedule (Legal) ✅
1. Open a contract with 90+ days overdue
2. Click: **Send 4th Schedule** button
3. **Expected Result:**
   - Email sent
   - Status changed to **Legal Action**
   - Date recorded

#### Test 3.6: Issue Repossession Order ✅
1. Open a contract in legal action
2. Click: **Issue Repo Order** button
3. Confirm action
4. **Expected Result:**
   - Contract status → **Repossessed**
   - Asset status → **Repossessed**
   - Chatter log updated

#### Test 3.7: Attempt to Create Contract ❌ (Should Fail)
1. Navigate to: **Asset Finance → Operations → Contracts**
2. Click: **Create** button
3. **Expected Result:** Access error or button not visible

#### Test 3.8: Attempt to Approve ❌ (Should Fail)
1. Open any active contract
2. **Expected Result:** No **Approve** or **Disburse** buttons visible

#### Test 3.9: Batch Send Reminders ✅
1. Navigate to contracts list
2. Select multiple active contracts (checkbox)
3. Click: **Action → Batch Send Reminders**
4. **Expected Result:** Reminders sent to all selected contracts

---

## Sample Test Data

### Quick Setup Script (Run as Admin)

Create sample data for testing:

#### Sample Customer (Hirer)
```
Name: John Doe Test
Email: john.doe@test.com
Phone: +65 1234 5678
NRIC: S1234567A
Customer Type: Individual
Is Finance Customer: ✅
```

#### Sample Guarantor
```
Name: Jane Smith Test
Email: jane.smith@test.com
Phone: +65 8765 4321
NRIC: S7654321B
Is Finance Guarantor: ✅
```

#### Sample Vehicle (Asset)
```
License Plate: SXX1234A
Make: Toyota
Model: Corolla Altis
Year: 2023
Chassis No: JTDBT923X71234567
Engine No: 2ZR-1234567
Purchase Price: $50,000
```

#### Sample Financial Product
```
Name: HP 5-Year Standard
Product Type: Hire Purchase
Default Interest Rate: 8.5%
Min Term: 12 months
Max Term: 60 months
Step: 12 months
Active: ✅
```

#### Sample Contract (Full Example)
```
Agreement No: AUTO-GENERATED
Product: HP 5-Year Standard
Asset: SXX1234A (Toyota Corolla)
Hirer: John Doe Test
Agreement Date: Today
Cash Price: $50,000
Down Payment: $10,000
Loan Amount: $40,000 (computed)
Interest Rate: 8.5%
No. of Installments: 60 Months
Installment Type: Annuity/Standard
Interest Method: Rule of 78
Payment Scheme: Arrears
First Due Date: Next month
Status: Draft → Active → Closed
```

---

## Testing Checklist

### Pre-Testing Setup ✅
- [ ] All 3 test users created
- [ ] User passwords recorded
- [ ] Sample customer created
- [ ] Sample asset created
- [ ] Financial product configured
- [ ] Chart of accounts configured
- [ ] Email server configured (for email tests)

### Finance Officer Tests ✅
- [ ] Can login successfully
- [ ] Can view dashboard
- [ ] Can create contracts
- [ ] Can edit draft contracts
- [ ] Can generate schedules
- [ ] Cannot approve contracts
- [ ] Cannot disburse funds
- [ ] Cannot delete contracts
- [ ] Cannot access settings

### Finance Manager Tests ✅
- [ ] Can login successfully
- [ ] Can perform all Officer tasks
- [ ] Can approve contracts
- [ ] Can disburse funds
- [ ] Can create invoices
- [ ] Can process settlements
- [ ] Can delete contracts
- [ ] Can configure settings
- [ ] Can view all reports

### Collection Staff Tests ✅
- [ ] Can login successfully
- [ ] Can view active/repo contracts only
- [ ] Cannot view draft/closed contracts
- [ ] Can view dashboard
- [ ] Can send payment reminders
- [ ] Can send overdue notices
- [ ] Can send 4th schedule
- [ ] Can issue repo orders
- [ ] Can send batch reminders
- [ ] Cannot create contracts
- [ ] Cannot approve/disburse
- [ ] Cannot access settings

---

## Troubleshooting

### Issue 1: User Cannot See Asset Finance Menu
**Problem:** After login, Asset Finance menu not visible

**Solution:**
1. Logout and login as Admin
2. Go to Settings → Users → Users
3. Edit the affected user
4. Verify **Asset Financing** group is assigned
5. Save user
6. **Important:** User must logout and login again for changes to take effect

---

### Issue 2: Buttons Not Visible/Disabled
**Problem:** Expected buttons (Approve, Disburse) not showing

**Solution:**
1. Check user's security group
2. Approve button requires: **Finance Manager** group
3. Disburse button requires: **Finance Manager** group + Contract must be **Active**
4. Some buttons only appear in specific contract states

---

### Issue 3: Access Denied Error
**Problem:** "Access Denied" error when trying to perform action

**Expected Behavior:**
- This is correct if user lacks permissions
- Example: Officer trying to approve → Access Denied ✅ Correct
- Example: Collection trying to create → Access Denied ✅ Correct

**If Unexpected:**
1. Verify user has correct group assigned
2. Check record rules in Settings → Technical → Security → Record Rules
3. Verify `ir.model.access.csv` has correct permissions

---

### Issue 4: Collection Staff Sees All Contracts
**Problem:** Collection staff can see draft/closed contracts

**Solution:**
1. Go to: Settings → Technical → Security → Record Rules
2. Find: "Finance Contract: Collection Access"
3. Verify domain: `[('ac_status', 'in', ['active', 'repo'])]`
4. If rule missing, update module

---

### Issue 5: Email Not Sending
**Problem:** Collection notices not sending emails

**Solution:**
1. Configure outgoing email server
2. Go to: Settings → Technical → Email → Outgoing Mail Servers
3. Add SMTP configuration:
   ```
   SMTP Server: smtp.gmail.com (example)
   SMTP Port: 587
   Security: TLS
   Username: your-email@gmail.com
   Password: app-specific-password
   ```
4. Click: **Test Connection**
5. Ensure hirer has valid email address

---

### Issue 6: Settings Menu Not Visible
**Problem:** Finance Manager cannot see Configuration → Settings

**Solution:**
1. User needs: **Administration / Settings** access
2. Edit user → Access Rights
3. Find: **Administration** section
4. Select: **Settings**
5. Save and re-login

---

### Issue 7: Dashboard Shows No Data
**Problem:** Dashboard KPIs all show zero

**Reason:** No active contracts exist

**Solution:**
1. Login as Finance Manager
2. Create and approve at least one contract
3. Refresh dashboard
4. Data should appear

---

## Advanced Testing Scenarios

### Scenario A: Full Contract Lifecycle
**Test all roles together:**

1. **Officer** creates contract in draft
2. **Manager** approves and disburses
3. **Manager** creates invoices
4. System (cron) calculates penalties (simulate overdue)
5. **Collection** sends reminder emails
6. **Manager** processes payment
7. **Collection** monitors aging
8. **Manager** processes early settlement

---

### Scenario B: Collection Escalation Path
**Test collection workflow:**

1. Create contract with past due dates (Manager)
2. Contract becomes overdue (wait or modify dates)
3. Collection sends: Payment Reminder
4. Wait 30 days (or modify dates)
5. Collection sends: Overdue Notice
6. Wait 60 days → Status changes to **Attention**
7. Collection sends: 4th Schedule → Status changes to **Legal**
8. Wait 90 days → Collection issues **Repo Order**
9. Status changes to **Repossessed**
10. Collection sends: 5th Schedule

---

### Scenario C: Payment Allocation Testing
**Test waterfall logic:**

1. Create contract with overdue installments and penalties
2. Contract has:
   - $500 in penalties
   - $2,000 overdue (2 installments)
   - $1,000 current installment
3. Register payment of $1,000
4. Verify allocation:
   - $500 → Penalties (first)
   - $500 → Oldest overdue installment
   - $0 → Current installment
5. Check Payment Allocation tab for breakdown

---

## Security Verification Commands

### Check User Groups (Python Console)
```python
# Login as Admin → Settings → Technical → Python Console
user = self.env['res.users'].search([('login', '=', 'finance.officer@test.com')])
print(user.groups_id.mapped('name'))
# Should include: 'Finance Officer'
```

### Check Record Rules
```python
# View all finance contract rules
rules = self.env['ir.rule'].search([('model_id.model', '=', 'finance.contract')])
for rule in rules:
    print(f"{rule.name}: {rule.domain_force}")
```

### Verify Access Rights
```python
# Check what models user can access
user = self.env['res.users'].browse(USER_ID)
self.env['ir.model.access'].check('finance.contract', 'write', raise_exception=False)
```

---

## Test Data Export/Import

### Export Test Data (for sharing)
1. Navigate to each model (Contracts, Customers, Assets)
2. Select records
3. Click: Action → Export
4. Select fields
5. Save as CSV

### Import Test Data
1. Navigate to list view
2. Click: Action → Import
3. Upload CSV
4. Map fields
5. Click: Import

---

## Production Deployment Notes

### Before Going Live:
1. ⚠️ **Delete all test users**
2. ⚠️ **Delete test contracts/data**
3. ⚠️ **Change all passwords**
4. ⚠️ **Configure real email server**
5. ⚠️ **Verify accounting accounts**
6. ⚠️ **Backup database**
7. ⚠️ **Test with real (small) transaction first**

### Security Hardening:
1. Enforce strong passwords
2. Enable two-factor authentication
3. Set password expiration policy
4. Audit user activity logs
5. Restrict settings access
6. Review record rules
7. Enable database backup schedule

---

## Quick Reference Card

| Role | Login | Password | Can Do | Cannot Do |
|------|-------|----------|---------|-----------|
| **Officer** | `finance.officer@test.com` | `test123` | Create, Edit, View | Approve, Disburse, Delete |
| **Manager** | `finance.manager@test.com` | `manager123` | Everything | (No restrictions) |
| **Collection** | `collection.staff@test.com` | `collect123` | View Active, Send Notices | Create, Approve, Edit |

---

## Support & Documentation

### Additional Resources:
- **Module Documentation**: See `IMPROVEMENTS.md`
- **Dashboard Guide**: See `DASHBOARD_GUIDE.md`
- **Changelog**: See `CHANGELOG.md`
- **Refactoring Summary**: See `REFACTORING_SUMMARY.md`

### Need Help?
- Check Odoo logs: Settings → Technical → Logging
- Enable debug mode for detailed errors
- Review chatter logs on records
- Check audit trail in user logs

---

**Version**: 1.0
**Last Updated**: 2025-12-10
**Module**: Asset Financing Management
**Odoo Version**: 19

---

**Important Reminder:** These are **testing accounts only**. Never use these credentials or simple passwords in production environments!
