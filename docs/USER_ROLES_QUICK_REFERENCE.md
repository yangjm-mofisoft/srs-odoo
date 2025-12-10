# User Roles Quick Reference - Asset Finance Module

## Quick Navigation Menu

After restart, you can now access Users from:

```
Asset Finance → Configuration → Users
```

---

## 3 Security Groups Visual Guide

### 1️⃣ Finance Officer (Basic Access)

```
┌─────────────────────────────────────┐
│     👤 FINANCE OFFICER              │
│     (Data Entry Level)              │
├─────────────────────────────────────┤
│                                     │
│  ✅ CAN DO:                         │
│  • Create contracts                 │
│  • Edit draft contracts             │
│  • View active contracts            │
│  • Generate schedules               │
│  • Create invoices                  │
│  • View dashboard                   │
│  • View payments                    │
│                                     │
│  ❌ CANNOT DO:                      │
│  • Approve contracts                │
│  • Close contracts                  │
│  • Delete contracts                 │
│  • Access repo contracts            │
│  • Change settings                  │
│                                     │
│  👥 BEST FOR:                       │
│  • Junior staff                     │
│  • Data entry clerks                │
│  • Contract coordinators            │
│                                     │
└─────────────────────────────────────┘
```

---

### 2️⃣ Finance Manager (Full Access)

```
┌─────────────────────────────────────┐
│     👔 FINANCE MANAGER              │
│     (Full Control)                  │
├─────────────────────────────────────┤
│                                     │
│  ✅ ALL OFFICER PERMISSIONS +       │
│                                     │
│  • ✅ Approve contracts             │
│  • ✅ Close contracts               │
│  • ✅ Delete contracts              │
│  • ✅ Access all statuses           │
│  • ✅ Manage master data            │
│  • ✅ Change settings               │
│  • ✅ Create disbursements          │
│  • ✅ Process settlements           │
│  • ✅ Manage penalty rules          │
│  • ✅ View all reports              │
│                                     │
│  👥 BEST FOR:                       │
│  • Department heads                 │
│  • Senior managers                  │
│  • Finance directors                │
│                                     │
└─────────────────────────────────────┘
```

---

### 3️⃣ Collection Staff (Recovery Access)

```
┌─────────────────────────────────────┐
│     📞 COLLECTION STAFF             │
│     (Recovery Functions)            │
├─────────────────────────────────────┤
│                                     │
│  ✅ CAN DO:                         │
│  • View active contracts (overdue)  │
│  • View repo contracts              │
│  • Send payment reminders           │
│  • Send overdue notices             │
│  • Send 4th schedule (legal)        │
│  • Send 5th schedule (post-repo)    │
│  • Issue repo orders                │
│  • Update collection dates          │
│  • View penalties                   │
│                                     │
│  ❌ CANNOT DO:                      │
│  • Create contracts                 │
│  • Edit contract terms              │
│  • Approve/close contracts          │
│  • Delete records                   │
│  • View draft contracts             │
│  • Access settings                  │
│                                     │
│  👥 BEST FOR:                       │
│  • Collection agents                │
│  • Recovery team                    │
│  • Call center staff                │
│                                     │
└─────────────────────────────────────┘
```

---

## How to Add User (Step-by-Step)

### 🎯 Quick Steps (5 Minutes)

```
Step 1: Navigate
========================================
Method A: Settings → Users → Create
Method B: Asset Finance → Configuration → Users → Create

Step 2: Basic Info
========================================
Name:  [John Doe              ]
Email: [john.doe@company.com  ]
Phone: [+65 1234 5678         ]

Step 3: Choose Role (Access Rights Tab)
========================================
Asset Finance:
  ☐ Finance Officer    ← Check for basic user
  ☐ Finance Manager    ← Check for manager
  ☐ Collection Staff   ← Check for collection

Step 4: Save & Notify
========================================
[Save] button → Send password reset email
```

---

## How to Change User Role

### Scenario A: Promote Officer to Manager

```
1. Open user record
2. Access Rights tab
3. Asset Finance section:
   ☑️ Finance Officer   (keep checked)
   ☑️ Finance Manager   (ADD this)
4. [Save]
5. User must logout/login
```

### Scenario B: Change to Collection Staff

```
1. Open user record
2. Access Rights tab
3. Asset Finance section:
   ☐ Finance Officer   (UNCHECK)
   ☐ Finance Manager   (UNCHECK)
   ☑️ Collection Staff (CHECK)
4. [Save]
5. User must logout/login
```

---

## Access Comparison Matrix

| Feature | 👤 Officer | 👔 Manager | 📞 Collection |
|---------|-----------|-----------|--------------|
| **Contracts** | | | |
| Create | ✅ | ✅ | ❌ |
| Edit Draft | ✅ | ✅ | ❌ |
| Approve | ❌ | ✅ | ❌ |
| Close | ❌ | ✅ | ❌ |
| Delete | ❌ | ✅ | ❌ |
| View Active | ✅ All | ✅ All | ✅ Overdue only |
| View Repo | ❌ | ✅ | ✅ |
| **Operations** | | | |
| Generate Schedule | ✅ | ✅ | ❌ |
| Create Invoices | ✅ | ✅ | ❌ |
| Record Payments | ✅ | ✅ | ❌ |
| **Collections** | | | |
| Send Reminders | ❌ | ✅ | ✅ |
| Send Notices | ❌ | ✅ | ✅ |
| 4th Schedule | ❌ | ✅ | ✅ |
| 5th Schedule | ❌ | ✅ | ✅ |
| Issue Repo | ❌ | ✅ | ✅ |
| **Master Data** | | | |
| Products | ❌ | ✅ | ❌ |
| Penalty Rules | ❌ | ✅ | ❌ |
| Terms | ❌ | ✅ | ❌ |
| **Settings** | | | |
| Module Settings | ❌ | ✅ | ❌ |
| Users | ❌ | Admin only | ❌ |

---

## Common User Configurations

### 👤 Data Entry Clerk
```
Role: Finance Officer
Additional: None
Use case: Daily contract entry
```

### 👔 Finance Team Lead
```
Role: Finance Officer + Manager
Additional: Accounting / Adviser
Use case: Can do everything + approve
```

### 📞 Recovery Agent
```
Role: Collection Staff
Additional: None
Use case: Call overdue customers only
```

### 🎯 Senior Officer with Collection
```
Role: Finance Officer + Collection Staff
Additional: Contact Creation
Use case: Contracts + can handle collections
```

### 💼 Department Head
```
Role: Finance Manager
Additional: Settings / Technical Features
Use case: Full control + admin tasks
```

---

## Troubleshooting Quick Fixes

### ❌ "Cannot see Asset Finance menu"
```
✅ FIX: Assign at least one role:
   - Finance Officer, OR
   - Finance Manager, OR
   - Collection Staff
   Then logout/login
```

### ❌ "Access Denied" error
```
✅ FIX: Check user has correct role
   Check user is Active (not archived)
   Verify correct Company assigned
```

### ❌ "Users menu not visible in Configuration"
```
✅ FIX: This is normal!
   Only ADMINISTRATORS can see Users menu
   Regular users cannot manage users
```

### ❌ "Permission changes not working"
```
✅ FIX:
   1. Save user record
   2. User must LOGOUT completely
   3. User must LOGIN again
   4. Close all browser tabs
   5. Clear cache (Ctrl+F5)
```

---

## Real-World Examples

### Example 1: New Employee Onboarding

**Sarah joins as Finance Officer**

```
Day 1 - Setup:
✅ Create user: sarah.chen@company.com
✅ Role: Finance Officer
✅ Password: Send reset email
✅ Access: Contact Creation
✅ Status: Active

Day 1 - Test:
✅ Sarah logs in
✅ Creates test contract
✅ Generates schedule
✅ CANNOT approve (expected)

Result: ✅ Working correctly
```

---

### Example 2: Staff Promotion

**Mike promoted from Officer to Manager**

```
Before:
Role: Finance Officer
Can: Create, edit drafts
Cannot: Approve, delete

Update:
✅ Open Mike's user
✅ Add Finance Manager role
✅ Keep Finance Officer checked
✅ Save
✅ Mike logs out and back in

After:
Role: Finance Officer + Manager
Can: Everything!
Result: ✅ Promotion successful
```

---

### Example 3: New Collection Team

**Hiring 3 collection agents**

```
Agent 1: David Lee
✅ Create user: david.lee@company.com
✅ Role: Collection Staff ONLY
✅ Access: Basic (no additional)

Agent 2: Lisa Wong
✅ Create user: lisa.wong@company.com
✅ Role: Collection Staff ONLY
✅ Access: Basic (no additional)

Agent 3: Tom Harris
✅ Create user: tom.harris@company.com
✅ Role: Collection Staff ONLY
✅ Access: Basic (no additional)

Result: ✅ All can access overdue contracts
        ✅ All can send reminders
        ✅ None can modify contracts
```

---

## Testing Checklist

After creating a user, test these:

### ✅ Finance Officer Test
- [ ] Can login successfully
- [ ] Can see Asset Finance menu
- [ ] Can create new contract
- [ ] Can generate schedule
- [ ] CANNOT approve (should fail)
- [ ] Can view dashboard

### ✅ Finance Manager Test
- [ ] Can do all Officer tasks
- [ ] Can approve contracts
- [ ] Can close contracts
- [ ] Can delete contracts
- [ ] Can access Settings
- [ ] Can view all statuses

### ✅ Collection Staff Test
- [ ] Can login successfully
- [ ] Can see overdue contracts
- [ ] Can send reminders
- [ ] CANNOT create contracts
- [ ] CANNOT see draft contracts
- [ ] Can issue repo orders

---

## Security Best Practices

### ✅ DO:
- Give minimum required permissions
- Review user access quarterly
- Use different roles for different functions
- Enable password reset on first login
- Test permissions after creation

### ❌ DON'T:
- Give everyone Manager access
- Share login credentials
- Keep inactive users active
- Use generic passwords
- Skip permission testing

---

## Quick Commands

### Create Test Users (Example)
```python
# Via Odoo shell (for testing)
officer = env['res.users'].create({
    'name': 'Test Officer',
    'login': 'officer@test.com',
    'groups_id': [(6, 0, [
        env.ref('asset_finance.group_finance_officer').id
    ])]
})
```

### Check User Permissions
```python
# In Python
user = env.user
has_officer = user.has_group('asset_finance.group_finance_officer')
has_manager = user.has_group('asset_finance.group_finance_manager')
has_collection = user.has_group('asset_finance.group_finance_collection')
```

---

## Summary

### ✅ NEW Feature Added
You can now access Users from:
```
Asset Finance → Configuration → Users
```

### 3 Simple Roles
1. **Officer** = Data entry
2. **Manager** = Full control
3. **Collection** = Recovery only

### Quick Access
- **Settings** → Users (global)
- **Asset Finance** → Configuration → Users (NEW!)

### Remember
- Always test after creating users
- Users must logout/login after role changes
- Only admins can see Users menu

---

For detailed instructions, see [USER_MANAGEMENT_GUIDE.md](USER_MANAGEMENT_GUIDE.md)

**Version**: 1.0
**Updated**: 2025-12-10
