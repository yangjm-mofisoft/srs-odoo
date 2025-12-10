# User Management Guide - Asset Finance Module

## Overview
This guide explains how to add users and manage user roles in the Asset Finance module.

**Module**: Asset Financing Management
**Version**: 1.1.0
**Last Updated**: 2025-12-10

---

## Table of Contents
1. [Understanding Security Groups](#understanding-security-groups)
2. [Adding New Users](#adding-new-users)
3. [Changing User Roles](#changing-user-roles)
4. [Quick Access Methods](#quick-access-methods)
5. [Common Scenarios](#common-scenarios)
6. [Troubleshooting](#troubleshooting)

---

## Understanding Security Groups

The Asset Finance module has **3 security groups** with different permission levels:

### 1. 👤 Finance Officer (Basic Access)

**What they can do**:
- ✅ Create new contracts
- ✅ Edit draft contracts
- ✅ View active contracts
- ✅ Generate schedules
- ✅ View payments
- ✅ Access dashboard

**What they CANNOT do**:
- ❌ Approve contracts
- ❌ Close contracts
- ❌ Delete contracts
- ❌ Access repo contracts
- ❌ View sensitive financial data

**Best for**: Data entry staff, junior finance officers

---

### 2. 👔 Finance Manager (Full Access)

**What they can do**:
- ✅ **All Finance Officer permissions**
- ✅ Approve contracts
- ✅ Close contracts
- ✅ Delete contracts
- ✅ Access all contract statuses (draft, active, closed, repo)
- ✅ Manage master data (products, terms, penalty rules)
- ✅ View all financial reports
- ✅ Access settings

**Best for**: Senior finance managers, department heads

---

### 3. 📞 Collection Staff (Collection Access)

**What they can do**:
- ✅ View active contracts (payment status = not paid)
- ✅ View repo contracts
- ✅ Send payment reminders
- ✅ Send overdue notices
- ✅ Issue 4th and 5th schedules
- ✅ Update collection dates
- ✅ View penalties

**What they CANNOT do**:
- ❌ Create new contracts
- ❌ Edit contract terms
- ❌ Approve or close contracts
- ❌ Delete records
- ❌ Access draft contracts

**Best for**: Collection agents, recovery team

---

## Adding New Users

### Method 1: Via Settings Menu (Global)

#### Step 1: Navigate to Users
1. **Login as Administrator**
2. Click **Settings** (⚙️) in the top navigation
3. Go to **Users & Companies** → **Users**

#### Step 2: Create User
1. Click **Create** button
2. Fill in **basic information**:
   ```
   Name: John Doe
   Email: john.doe@company.com
   Phone: +65 1234 5678
   ```

#### Step 3: Set Password
1. Scroll to **Account Security** section
2. Click **Send reset password instructions** OR
3. Manually set password in the field

#### Step 4: Assign Asset Finance Role
1. Go to **Access Rights** tab
2. Scroll down to find **Asset Finance** section
3. Check the appropriate box:
   - ☑️ **Finance Officer** (for basic users)
   - ☑️ **Finance Manager** (for managers)
   - ☑️ **Collection Staff** (for collection team)

#### Step 5: Additional Permissions
You may also want to assign:
- **Contact Creation** - If they need to add customers
- **Fleet / Manager** - If they manage vehicles
- **Accounting** - For journal entry access

#### Step 6: Save
Click **Save** button at the top

---

### Method 2: Via Asset Finance Module (NEW!)

#### Step 1: Navigate to Users in Asset Finance
1. **Login as Administrator**
2. Go to **Asset Finance** → **Configuration** → **Users**

#### Step 2: Follow Same Steps as Method 1
The form is identical, just accessed from a different location!

---

## Changing User Roles

### Scenario 1: Promote Finance Officer to Manager

1. Go to **Settings** → **Users & Companies** → **Users**
2. Open the user record (e.g., "Sarah Smith")
3. Go to **Access Rights** tab
4. Check ☑️ **Finance Manager** (keep Finance Officer checked too)
5. Click **Save**

**Result**: Sarah now has full manager permissions

---

### Scenario 2: Change Manager to Collection Staff

1. Open the user record
2. Go to **Access Rights** tab
3. **Uncheck** ☐ Finance Officer
4. **Uncheck** ☐ Finance Manager
5. **Check** ☑️ Collection Staff
6. Click **Save**

**Result**: User can only access collection features

---

### Scenario 3: Give Officer Additional Collection Access

1. Open the user record
2. Go to **Access Rights** tab
3. Keep ☑️ Finance Officer
4. Also check ☑️ Collection Staff
5. Click **Save**

**Result**: User has both officer and collection permissions

---

## Quick Access Methods

### Access Path 1: Settings Menu
```
Settings (⚙️) → Users & Companies → Users
```

### Access Path 2: Asset Finance Module (NEW!)
```
Asset Finance → Configuration → Users
```

### Access Path 3: Direct URL
```
http://localhost:8069/web#action=base.action_res_users&model=res.users&view_type=list
```

---

## Common Scenarios

### Scenario 1: New Employee - Finance Officer

**User**: Mike Chen (Finance Officer)

**Steps**:
1. Create user with email `mike.chen@company.com`
2. Set temporary password
3. Access Rights:
   - ☑️ Finance Officer
   - ☐ Finance Manager
   - ☐ Collection Staff
4. Additional: ☑️ Contact Creation
5. Save and send password reset email

**Mike can now**:
- Create contracts
- Edit draft contracts
- View dashboard
- Generate schedules

---

### Scenario 2: Promotion - Officer to Manager

**User**: Sarah Thompson (currently Officer, promoted to Manager)

**Steps**:
1. Open Sarah's user record
2. Access Rights:
   - ☑️ Finance Officer (keep checked)
   - ☑️ Finance Manager (add this)
   - ☐ Collection Staff
3. Save

**Sarah can now**:
- Everything she could do before
- **PLUS** approve/close contracts
- **PLUS** delete records
- **PLUS** access settings

---

### Scenario 3: New Collection Agent

**User**: David Lee (Collection Agent)

**Steps**:
1. Create user with email `david.lee@company.com`
2. Access Rights:
   - ☐ Finance Officer
   - ☐ Finance Manager
   - ☑️ Collection Staff
3. Save

**David can now**:
- View active contracts (overdue only)
- Send payment reminders
- Send 4th/5th schedules
- Issue repo orders
- View penalties

---

### Scenario 4: Temporary Manager Access

**User**: Jane Doe (Officer needs temporary manager access)

**Steps**:
1. Open Jane's user record
2. Add ☑️ Finance Manager
3. Set **Expiration Date** (if you want to limit access)
4. Save

**To revoke later**:
1. Uncheck ☐ Finance Manager
2. Save

---

## Permission Matrix

| Action | Finance Officer | Finance Manager | Collection Staff |
|--------|----------------|-----------------|------------------|
| View Dashboard | ✅ Yes | ✅ Yes | ✅ Yes |
| Create Contracts | ✅ Yes | ✅ Yes | ❌ No |
| Edit Draft | ✅ Yes | ✅ Yes | ❌ No |
| Approve Contracts | ❌ No | ✅ Yes | ❌ No |
| Close Contracts | ❌ No | ✅ Yes | ❌ No |
| Delete Contracts | ❌ No | ✅ Yes | ❌ No |
| View Active | ✅ Yes | ✅ Yes | ✅ Yes (overdue) |
| View Repo | ❌ No | ✅ Yes | ✅ Yes |
| Send Reminders | ❌ No | ✅ Yes | ✅ Yes |
| Issue Repo Order | ❌ No | ✅ Yes | ✅ Yes |
| Manage Products | ❌ No | ✅ Yes | ❌ No |
| Access Settings | ❌ No | ✅ Yes | ❌ No |

---

## Troubleshooting

### Issue 1: User Cannot See Asset Finance Menu

**Problem**: User logs in but doesn't see "Asset Finance" in the menu

**Solution**:
1. Check if user has at least ONE of these roles:
   - Finance Officer
   - Finance Manager
   - Collection Staff
2. If not, assign appropriate role
3. Have user **logout and login again**
4. Clear browser cache (Ctrl+F5)

---

### Issue 2: User Cannot See Users Menu

**Problem**: Users menu not visible in Asset Finance → Configuration

**Solution**:
- Only **Administrators** (Settings access) can see this menu
- This is by design for security
- Non-admins should request admin to create/modify users

---

### Issue 3: User Has Access But Gets "Access Denied"

**Problem**: User has role but gets "Access Denied" error

**Solution**:
1. Check if correct **company** is assigned
2. Verify user is **active** (not archived)
3. Check **record rules** - might be filtered by status
4. For collection staff: They can only see active/repo contracts

---

### Issue 4: Cannot Find Asset Finance in Access Rights

**Problem**: Cannot find "Asset Finance" section in Access Rights tab

**Solution**:
1. Ensure module is **installed**
2. **Upgrade** the module:
   ```bash
   docker-compose restart web
   ```
3. Refresh browser (Ctrl+F5)
4. If still missing, reinstall module

---

### Issue 5: User Permissions Not Taking Effect

**Problem**: Assigned role but permissions haven't changed

**Solution**:
1. **Save** the user record
2. User must **logout** completely
3. User must **login again**
4. If using multiple tabs, **close all tabs**
5. Restart browser if needed

---

## Security Best Practices

### 1. Principle of Least Privilege
- ✅ Give users ONLY the permissions they need
- ❌ Don't give everyone Manager access

### 2. Role Separation
- ✅ Separate data entry (Officer) from approval (Manager)
- ✅ Separate collection staff from contract creation
- ✅ Have different users for different functions

### 3. Regular Audits
- Review user list quarterly
- Remove inactive users
- Check for unused accounts
- Verify permissions are still appropriate

### 4. Password Policy
- Require strong passwords
- Enable two-factor authentication (2FA)
- Force password changes periodically
- Send password reset on first login

### 5. Access Logging
- Monitor user activity
- Review audit logs regularly
- Check for unusual access patterns

---

## Testing User Roles

### Test Plan for New Users

After creating a user, test their access:

#### For Finance Officer:
1. ✅ Can create new contract
2. ✅ Can generate schedule
3. ❌ Cannot approve contract (should get error)
4. ❌ Cannot delete contract (button hidden)

#### For Finance Manager:
1. ✅ Can do everything Officer can
2. ✅ Can approve contracts
3. ✅ Can close contracts
4. ✅ Can access Settings

#### For Collection Staff:
1. ❌ Cannot see "Contracts" menu (or sees empty list)
2. ✅ Can access collection functions
3. ✅ Can send reminders
4. ❌ Cannot create contracts (button hidden)

---

## User Onboarding Checklist

When adding a new user, complete this checklist:

- [ ] Create user account
- [ ] Set temporary password
- [ ] Assign appropriate role
- [ ] Assign to correct company
- [ ] Add additional permissions (if needed)
- [ ] Send password reset email
- [ ] Provide user guide/training
- [ ] Test user access
- [ ] Document user role in system
- [ ] Add to team contact list

---

## Quick Reference Card

### User Creation Quick Steps
```
1. Settings → Users & Companies → Users
2. Click Create
3. Fill: Name, Email, Phone
4. Access Rights → Check role
5. Save
6. Send password reset
```

### Role Assignment Quick Steps
```
1. Open user record
2. Access Rights tab
3. Asset Finance section:
   - Officer = Basic
   - Manager = Full
   - Collection = Limited
4. Save
5. User logout/login
```

### Access Levels Summary
```
Officer    = Create + Edit drafts
Manager    = Officer + Approve + Close + Delete
Collection = View overdue + Send reminders
```

---

## Support & Additional Help

### Related Documentation
- [TESTING_ACCOUNTS_GUIDE.md](TESTING_ACCOUNTS_GUIDE.md) - Manual testing with different roles
- [VISUAL_TESTING_GUIDE.md](VISUAL_TESTING_GUIDE.md) - Security hierarchy diagrams
- [ADVANCED_TESTING_SCENARIOS.md](ADVANCED_TESTING_SCENARIOS.md) - Multi-user scenarios

### Need Help?
- Check Odoo documentation: https://www.odoo.com/documentation
- Review security groups in: `security/security.xml`
- Review access rules in: `security/ir.model.access.csv`

---

## Appendix: Technical Details

### Security Group XML IDs
```xml
asset_finance.group_finance_officer
asset_finance.group_finance_manager
asset_finance.group_finance_collection
```

### Menu Access
```xml
<!-- Users menu is restricted to administrators -->
<menuitem id="menu_finance_users"
          name="Users"
          groups="base.group_system"/>
```

### Checking User Role Programmatically
```python
# In Python code
user = self.env.user
is_officer = user.has_group('asset_finance.group_finance_officer')
is_manager = user.has_group('asset_finance.group_finance_manager')
is_collection = user.has_group('asset_finance.group_finance_collection')
```

---

**Document Version**: 1.0
**Created**: 2025-12-10
**Module**: Asset Financing Management
**Status**: ✅ Complete

---

## Summary

You now have multiple ways to manage users in your Asset Finance module:

1. ⚙️ **Settings → Users** (global access)
2. 💼 **Asset Finance → Configuration → Users** (module-specific, NEW!)
3. 🔗 **Direct URL** (bookmark for quick access)

Remember:
- **Finance Officer** = Basic data entry
- **Finance Manager** = Full access + approval
- **Collection Staff** = Recovery functions only

Always test user permissions after creating/modifying accounts!
