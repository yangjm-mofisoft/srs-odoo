# Security Management Guide - Groups vs Roles vs Privileges

## Overview
This guide explains the difference between Groups, Roles, and Privileges in Odoo, and shows you how to manage security through the UI instead of code.

**Module**: Asset Financing Management
**Version**: 1.1.0
**Last Updated**: 2025-12-10

---

## Table of Contents
1. [Understanding Odoo Security Concepts](#understanding-odoo-security-concepts)
2. [Groups vs Roles - What's the Difference?](#groups-vs-roles-whats-the-difference)
3. [UI-Based Security Management](#ui-based-security-management)
4. [Managing Access Rights in UI](#managing-access-rights-in-ui)
5. [When to Use Code vs UI](#when-to-use-code-vs-ui)
6. [Practical Examples](#practical-examples)

---

## Understanding Odoo Security Concepts

Odoo has **3 main security layers**:

### 1. **Security Groups** (aka "Roles")
- **What**: Named sets of permissions (e.g., "Finance Officer", "Finance Manager")
- **Where defined**: XML files (`security/security.xml`)
- **Assigned to**: Users (via Settings → Users → Access Rights tab)
- **Purpose**: Group users by job function

### 2. **Access Rights** (aka "Privileges")
- **What**: CRUD permissions (Create, Read, Update, Delete) per model
- **Where defined**: CSV files (`security/ir.model.access.csv`) OR **UI (NEW!)**
- **Linked to**: Security Groups
- **Purpose**: Control what each group can do with each model

### 3. **Record Rules**
- **What**: Filter which specific records a user can access
- **Where defined**: XML files OR **UI**
- **Purpose**: Row-level security (e.g., "only see your own contracts")

---

## Groups vs Roles - What's the Difference?

In Odoo, **Groups** and **Roles** are the **same thing**! Different terms for the same concept:

| Term | Used By | Meaning |
|------|---------|---------|
| **Security Group** | Odoo technical docs | Official Odoo terminology |
| **Role** | Business users | User-friendly term (Manager, Officer, etc.) |
| **Access Group** | Some modules | Alternative name |

**In this module, we use "Role" for user-facing documentation and "Group" in code.**

---

## UI-Based Security Management

### NEW Feature: Security Menu

After this update, you can now manage security directly from the UI:

```
Asset Finance → Configuration → Security
├── Access Rights     (CRUD permissions per model)
├── User Roles        (Manage security groups)
└── Record Rules      (Row-level filtering)
```

**Benefits**:
- ✅ No code changes required
- ✅ Changes take effect immediately
- ✅ No module upgrade needed
- ✅ Easier for non-technical users

---

## Managing Access Rights in UI

### Step 1: Navigate to Access Rights

```
Asset Finance → Configuration → Security → Access Rights
```

You'll see a list of all access rules for Asset Finance models:

| Name | Model | Security Group | Read | Write | Create | Delete |
|------|-------|----------------|------|-------|--------|--------|
| access.contract.officer | finance.contract | Finance Officer | ✓ | ✓ | ✓ | ✗ |
| access.contract.manager | finance.contract | Finance Manager | ✓ | ✓ | ✓ | ✓ |

### Step 2: Edit Permissions

Click on any row to edit:

**Example: Give Finance Officer delete permission**

1. Click on `access.contract.officer`
2. Check the **Delete** checkbox
3. Save

**Result**: Finance Officers can now delete contracts (no code change needed!)

### Step 3: Create New Access Rule

Click **Create** button:

```
Name: access.payment.collection_staff
Model: account.payment
Security Group: Collection Staff
Permissions:
  [✓] Read
  [✗] Write
  [✗] Create
  [✗] Delete
```

**Result**: Collection staff can view payments but not modify them.

---

## Managing User Roles (Security Groups)

### View Existing Roles

```
Asset Finance → Configuration → Security → User Roles
```

You'll see:
- Finance Officer
- Finance Manager
- Collection Staff

### Edit a Role

Click on **Finance Officer**:

**What you can configure**:
- **Name**: Display name
- **Users**: Which users have this role
- **Menus**: Which menus this role can access
- **Implied Groups**: Additional permissions to include
- **Access Rights**: Linked permissions (auto-populated)

### Create a New Role

Click **Create**:

```
Name: Finance Supervisor
Category: Asset Finance
Application: (leave blank)

Implied Groups:
  [✓] Finance Officer    (inherits all Officer permissions)

Users:
  [✓] John Doe
  [✓] Jane Smith
```

**Result**: New "Finance Supervisor" role created with Officer + custom permissions.

---

## When to Use Code vs UI

### Use **Code** (`ir.model.access.csv`) When:
- ✅ Permissions are **business logic** and shouldn't change
  - Example: "Collection staff can NEVER create contracts"
- ✅ You want **version control** of security rules
- ✅ You're deploying to **multiple instances** (dev, staging, prod)
- ✅ Security is part of **module installation**

### Use **UI** (Access Rights menu) When:
- ✅ Permissions may **vary by company/location**
  - Example: "Branch A allows Officers to delete, Branch B doesn't"
- ✅ You need **quick adjustments** without deploying code
- ✅ Non-technical users need to **manage permissions**
- ✅ Permissions are **data, not logic**

### Best Practice: **Hybrid Approach**

1. **Define base permissions in code** (CSV)
   - Ensures all installations have minimum required access
   - Version controlled and documented

2. **Allow UI customization** for edge cases
   - Admins can add/modify as needed
   - Changes don't require developer intervention

**Example**:
```csv
# Base permissions (in CSV - deployed with module)
access_contract_officer,Officer Access,finance.contract,group_finance_officer,1,1,1,0

# Then admin can add via UI:
# "Allow Officer to delete in Singapore branch" (created in UI)
```

---

## Practical Examples

### Example 1: New Role - "Finance Analyst"

**Requirement**: Create a read-only role that can view contracts and reports but not modify anything.

**Method 1: Via Code** (requires developer)

1. Edit `security/security.xml`:
```xml
<record id="group_finance_analyst" model="res.groups">
    <field name="name">Finance Analyst</field>
    <field name="category_id" ref="module_category_asset_finance"/>
</record>
```

2. Edit `security/ir.model.access.csv`:
```csv
access_contract_analyst,Analyst Contract,finance.contract,group_finance_analyst,1,0,0,0
access_payment_analyst,Analyst Payment,account.payment,group_finance_analyst,1,0,0,0
```

3. Upgrade module

**Method 2: Via UI** (no developer needed)

1. Go to: `Asset Finance → Configuration → Security → User Roles`
2. Click **Create**
3. Fill in:
   ```
   Name: Finance Analyst
   Category: Asset Finance
   ```
4. Save
5. Go to: `Asset Finance → Configuration → Security → Access Rights`
6. Click **Create** for each model:
   ```
   Name: access.contract.analyst
   Model: finance.contract
   Group: Finance Analyst
   Read: ✓
   Write: ✗
   Create: ✗
   Delete: ✗
   ```
7. Repeat for other models

**Result**: Same outcome, but UI method needs no code deployment!

---

### Example 2: Temporary Permission Grant

**Scenario**: Finance Officer needs delete permission for 1 week to clean up test data.

**Bad Approach**: Change code, deploy, then revert

**Good Approach**: Use UI

1. Go to: `Asset Finance → Configuration → Security → Access Rights`
2. Find `access.contract.officer`
3. Check **Delete** checkbox
4. Save
5. After 1 week: Uncheck **Delete**

**Benefit**: No code changes, instant effect, easily reversible.

---

### Example 3: Branch-Specific Permissions

**Scenario**: Singapore branch allows Officers to approve contracts, but Malaysia branch doesn't.

**Solution**: Use Record Rules (not Access Rights)

**Via UI**:
1. Go to: `Asset Finance → Configuration → Security → Record Rules`
2. Click **Create**
```
Name: Officer Can Approve (SG Only)
Model: finance.contract
Groups: Finance Officer
Domain: [('company_id.country_id.code', '=', 'SG')]
Permissions:
  Read: ✓
  Write: ✓
  Create: ✓
  Delete: ✗
```

**Result**: Officers in Singapore can approve, but not in Malaysia.

---

## Current Access Rights (As of v1.1.0)

### Finance Officer
| Model | Read | Write | Create | Delete |
|-------|------|-------|--------|--------|
| finance.contract | ✓ | ✓ | ✓ | ✗ |
| finance.contract.line | ✓ | ✓ | ✓ | ✗ |
| finance.asset | ✓ | ✓ | ✓ | ✗ |
| finance.product | ✓ | ✗ | ✗ | ✗ |
| account.payment | ✓ | ✓ | ✓ | ✗ |

### Finance Manager
| Model | Read | Write | Create | Delete |
|-------|------|-------|--------|--------|
| **All Officer permissions** | ✓ | ✓ | ✓ | ✓ |
| finance.product | ✓ | ✓ | ✓ | ✓ |
| finance.penalty.rule | ✓ | ✓ | ✓ | ✓ |
| res.config.settings | ✓ | ✓ | ✓ | ✗ |

### Collection Staff
| Model | Read | Write | Create | Delete |
|-------|------|-------|--------|--------|
| finance.contract | ✓ (filtered) | ✗ | ✗ | ✗ |
| account.payment | ✓ | ✗ | ✗ | ✗ |

**Note**: These can now be modified via UI without code changes!

---

## Viewing Current Permissions

### For a Specific User

1. Go to: `Settings → Users → [Select User]`
2. Click **Access Rights** tab
3. Scroll to **Asset Finance** section
4. See which roles are checked

### For a Specific Model

1. Go to: `Asset Finance → Configuration → Security → Access Rights`
2. Filter by Model: `finance.contract`
3. See all groups and their permissions

### For a Specific Role

1. Go to: `Asset Finance → Configuration → Security → User Roles`
2. Click on role (e.g., "Finance Officer")
3. See **Access Rights** tab for all permissions

---

## Security Audit Checklist

Use this checklist to review your security configuration:

- [ ] All users have appropriate roles assigned
- [ ] No users have excessive permissions (principle of least privilege)
- [ ] Test users can only access test data
- [ ] Collection staff cannot modify contracts
- [ ] Officers cannot approve their own contracts (if needed)
- [ ] Admins have restricted delete permissions on critical models
- [ ] Record rules are in place for multi-company setups
- [ ] Sensitive models (penalties, settings) are manager-only

---

## Troubleshooting

### Issue: Changes in UI Not Taking Effect

**Symptoms**: Modified access rights in UI but user still can't access

**Solution**:
1. User must **logout and login again**
2. Check browser cache (Ctrl+F5)
3. Verify access right was saved (check Access Rights menu)
4. Check if record rules are blocking access

---

### Issue: Can't See Security Menu

**Symptoms**: Security menu not visible in Configuration

**Solution**:
- Only **Administrators** (Settings access) can see Security menu
- Regular users (even Finance Managers) cannot access
- This is by design for security

---

### Issue: Access Right Conflicts

**Symptoms**: User has two roles with conflicting permissions

**Solution**:
- Odoo uses **OR logic** for permissions
- If ANY role grants access, user gets access
- Example: Officer (can't delete) + Manager (can delete) = **Can delete**
- Remove the more permissive role if not intended

---

## Migration from CSV to UI

If you want to **stop using CSV** and **manage everything in UI**:

### Step 1: Export Current Access Rights

1. Go to: `Asset Finance → Configuration → Security → Access Rights`
2. Select all Asset Finance access rights
3. **Export** (to have a backup)

### Step 2: Remove CSV File (Optional)

Edit `__manifest__.py`:
```python
'data': [
    'security/security.xml',
    # 'security/ir.model.access.csv',  # COMMENTED OUT
    'views/access_rights_views.xml',
    # ... other files
],
```

### Step 3: Recreate in UI

1. Upgrade module
2. Manually create access rights via UI based on CSV

**Pros**: Full UI control
**Cons**: Not version controlled, harder to deploy to multiple instances

**Recommendation**: Keep CSV for base permissions, use UI for customizations.

---

## Summary

### Key Takeaways

1. **Groups = Roles** (same concept, different names)
2. **Access Rights = Privileges** (CRUD permissions)
3. **Code (CSV)** = Version controlled, deployment-friendly
4. **UI** = Quick changes, no code required
5. **Best practice** = Base in code, customizations in UI

### Quick Reference

| Task | Location | Requires Admin |
|------|----------|----------------|
| Assign role to user | Settings → Users | Yes |
| Modify access rights | Asset Finance → Configuration → Security → Access Rights | Yes |
| Create new role | Asset Finance → Configuration → Security → User Roles | Yes |
| View my permissions | Settings → My Profile → Access Rights | No |

### New Menus Added

```
Asset Finance → Configuration
└── Security
    ├── Access Rights    (Manage CRUD permissions)
    ├── User Roles       (Manage security groups)
    └── Record Rules     (Row-level security)
```

---

## Additional Resources

- [USER_MANAGEMENT_GUIDE.md](USER_MANAGEMENT_GUIDE.md) - How to add users and assign roles
- [USER_ROLES_QUICK_REFERENCE.md](USER_ROLES_QUICK_REFERENCE.md) - Quick role comparison
- [security/security.xml](security/security.xml) - Group definitions
- [security/ir.model.access.csv](security/ir.model.access.csv) - Base access rights

---

**Document Version**: 1.0
**Created**: 2025-12-10
**Module**: Asset Financing Management
**Status**: ✅ Complete
