# Test Users Guide for Asset Finance Module

This guide explains how to create and use test users for testing the Asset Finance module's security and access rights.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Test Users Overview](#test-users-overview)
3. [Installation Methods](#installation-methods)
4. [Running Automated Tests](#running-automated-tests)
5. [Manual Testing Scenarios](#manual-testing-scenarios)
6. [Security Testing Checklist](#security-testing-checklist)

---

## 🚀 Quick Start

### Method 1: Using XML Data File (Easiest)

1. **Add test users data file to manifest:**

   Edit `__manifest__.py` and add the test users file:

   ```python
   'data': [
       'security/security.xml',
       'security/ir.model.access.csv',
       'data/sequence.xml',
       'data/test_users_data.xml',  # ← ADD THIS LINE (for testing only!)
       'data/cron.xml',
       # ... rest of files
   ],
   ```

2. **Upgrade the module:**

   ```bash
   docker-compose exec web python /odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo19 -u asset_finance --stop-after-init
   docker-compose restart web
   ```

3. **Login with test users:**

   Test users will be created with these credentials:
   - Login: `finance.manager` / Password: `test123`
   - Login: `finance.officer` / Password: `test123`
   - Login: `collection.staff` / Password: `test123`
   - Login: `finance.all` / Password: `test123`

### Method 2: Using Automated Tests

Run the test suite to verify access rights:

```bash
# Run all Asset Finance tests
docker-compose exec web python /odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo19 --test-enable --test-tags asset_finance --stop-after-init

# Run only user access tests
docker-compose exec web python /odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo19 --test-enable --test-tags asset_finance.test_user_access --stop-after-init
```

---

## 👥 Test Users Overview

### User 1: Finance Manager
- **Login:** `finance.manager`
- **Password:** `test123`
- **Email:** finance.manager@test.com
- **Groups:**
  - Finance Manager
  - Finance Officer (inherited)
  - Accounting Manager (implied)
  - Billing (implied through Officer)
- **Permissions:**
  - ✅ Full CRUD access to all contracts
  - ✅ Can approve contracts
  - ✅ Can process disbursements
  - ✅ Can create journal entries
  - ✅ Full access to accounting functions
  - ✅ Can manage chart of accounts

### User 2: Finance Officer
- **Login:** `finance.officer`
- **Password:** `test123`
- **Email:** finance.officer@test.com
- **Groups:**
  - Finance Officer
  - Billing (implied)
- **Permissions:**
  - ✅ Can create and manage contracts
  - ✅ Can view all contracts
  - ✅ Can create invoices
  - ❌ Cannot approve contracts
  - ❌ Cannot delete contracts
  - ❌ Cannot process disbursements
  - ❌ Cannot create journal entries

### User 3: Collection Staff
- **Login:** `collection.staff`
- **Password:** `test123`
- **Email:** collection.staff@test.com
- **Groups:**
  - Collection Staff
- **Permissions:**
  - ✅ Can view active/repo contracts only
  - ✅ Can update penalty information
  - ✅ Can send collection notices
  - ❌ Cannot see draft contracts
  - ❌ Cannot create contracts
  - ❌ Cannot delete contracts
  - ❌ Cannot approve contracts

### User 4: All Roles (Testing Super User)
- **Login:** `finance.all`
- **Password:** `test123`
- **Email:** finance.all@test.com
- **Groups:**
  - Finance Manager
  - Finance Officer
  - Collection Staff
- **Permissions:**
  - ✅ Has ALL permissions from all three roles
  - Useful for testing combined role scenarios

---

## 🛠️ Installation Methods

### Option A: XML Data File (Persistent Users)

**Pros:**
- ✅ Users persist across module upgrades
- ✅ Easy to create multiple users at once
- ✅ Can be version controlled
- ✅ `noupdate="1"` means won't be overwritten on upgrade

**Cons:**
- ⚠️ Must be removed before production deployment
- ⚠️ Users remain in database even after removing from manifest

**Steps:**

1. Add to `__manifest__.py`:
   ```python
   'data': [
       # ... existing files ...
       'data/test_users_data.xml',  # Add this
   ],
   ```

2. Upgrade module:
   ```bash
   docker-compose exec web python /odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo19 -u asset_finance --stop-after-init
   docker-compose restart web
   ```

3. Test users are created automatically

### Option B: Manual Creation via Odoo UI

**Pros:**
- ✅ Full control over user configuration
- ✅ No need to modify code
- ✅ Easy to delete when done

**Cons:**
- ❌ Time-consuming for multiple users
- ❌ Must recreate after database reset

**Steps:**

1. Login as Administrator
2. Go to **Settings → Users & Companies → Users**
3. Click **Create**
4. Fill in user details:
   - Name: Test Finance Manager
   - Email: finance.manager@test.com
   - Password: test123
5. Go to **Access Rights** tab
6. Under **Other → Asset Finance**, check **Finance Manager**
7. Click **Save**
8. Repeat for other roles

### Option C: Python Script via Odoo Shell

**Pros:**
- ✅ Quick one-time creation
- ✅ Can customize easily
- ✅ No code changes needed

**Cons:**
- ❌ Users lost on database reset
- ❌ Must run script manually

**Steps:**

```bash
# Open Odoo shell
docker-compose exec web python /odoo/odoo-bin shell -c /etc/odoo/odoo.conf -d odoo19
```

```python
# In Odoo shell, run:
# Create Finance Manager
env['res.users'].create({
    'name': 'Test Finance Manager',
    'login': 'finance.manager',
    'password': 'test123',
    'email': 'finance.manager@test.com',
    'groups_id': [(4, env.ref('asset_finance.group_finance_manager').id)],
})

# Create Finance Officer
env['res.users'].create({
    'name': 'Test Finance Officer',
    'login': 'finance.officer',
    'password': 'test123',
    'email': 'finance.officer@test.com',
    'groups_id': [(4, env.ref('asset_finance.group_finance_officer').id)],
})

# Create Collection Staff
env['res.users'].create({
    'name': 'Test Collection Staff',
    'login': 'collection.staff',
    'password': 'test123',
    'email': 'collection.staff@test.com',
    'groups_id': [(4, env.ref('asset_finance.group_collection_staff').id)],
})

env.cr.commit()  # Don't forget to commit!
exit()
```

---

## 🧪 Running Automated Tests

### Run All Tests

```bash
docker-compose exec web python /odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo19 --test-enable --test-tags asset_finance --stop-after-init
```

### Run Specific Test File

```bash
docker-compose exec web python /odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoo19 --test-enable --test-tags asset_finance.test_user_access --stop-after-init
```

### Test Coverage

The automated tests verify:
- ✅ User creation with correct groups
- ✅ Dashboard access for all roles
- ✅ Contract creation permissions
- ✅ Contract read permissions (record rules)
- ✅ Contract deletion permissions
- ✅ Implied groups (Accounting Manager, Billing)

---

## 🔍 Manual Testing Scenarios

### Scenario 1: Dashboard Access

**Test:** All users should be able to view the dashboard

1. Login as `finance.manager`
2. Click **Asset Finance → Dashboard**
3. ✅ Verify dashboard loads with KPIs
4. Logout
5. Repeat for `finance.officer` and `collection.staff`

### Scenario 2: Contract Creation

**Test:** Finance Manager and Officer can create, Collection Staff cannot

1. Login as `finance.manager`
2. Go to **Asset Finance → Operations → Contracts**
3. Click **Create**
4. Fill in contract details
5. Click **Save**
6. ✅ Verify contract is created
7. Logout
8. Login as `collection.staff`
9. Try to create a contract
10. ✅ Verify you get an access error or create button is hidden

### Scenario 3: Record Rules (Collection Staff)

**Test:** Collection Staff can only see active/repo contracts

**Setup:**
1. Login as Administrator
2. Create 3 contracts:
   - Contract A: Status = Draft
   - Contract B: Status = Active
   - Contract C: Status = Closed

**Test:**
1. Login as `collection.staff`
2. Go to **Asset Finance → Operations → Contracts**
3. ✅ Verify you only see Contract B (Active)
4. ✅ Verify you DON'T see Contract A (Draft) or C (Closed)

### Scenario 4: Approval Permission

**Test:** Only Finance Manager can approve contracts

1. Login as `finance.officer`
2. Open any draft contract
3. ✅ Verify **Approve** button is hidden or disabled
4. Logout
5. Login as `finance.manager`
6. Open the same contract
7. Click **Approve**
8. ✅ Verify status changes to Active

### Scenario 5: Menu Visibility

**Test:** Asset Finance menu should be visible to all three roles

1. Login as `finance.manager`
2. ✅ Verify **Asset Finance** menu appears in main menu
3. Logout and repeat for other users

---

## ✅ Security Testing Checklist

### Finance Manager
- [ ] Can access Dashboard
- [ ] Can create contracts
- [ ] Can edit contracts
- [ ] Can delete contracts
- [ ] Can approve contracts
- [ ] Can create journal entries
- [ ] Can access Chart of Accounts
- [ ] Can see all contracts (draft, active, closed)

### Finance Officer
- [ ] Can access Dashboard
- [ ] Can create contracts
- [ ] Can edit contracts
- [ ] **CANNOT** delete contracts
- [ ] **CANNOT** approve contracts
- [ ] **CANNOT** create journal entries
- [ ] Can create invoices
- [ ] Can see all contracts (draft, active, closed)

### Collection Staff
- [ ] Can access Dashboard
- [ ] **CANNOT** create contracts
- [ ] Can edit active contracts (penalties only)
- [ ] **CANNOT** delete contracts
- [ ] **CANNOT** approve contracts
- [ ] **ONLY** sees active/repo contracts
- [ ] **CANNOT** see draft or closed contracts

---

## 🗑️ Cleanup (Before Production)

### Remove Test Users Data File

1. Edit `__manifest__.py` and remove the test users line:
   ```python
   'data': [
       # ... other files ...
       # 'data/test_users_data.xml',  # ← REMOVE OR COMMENT THIS
   ],
   ```

2. Manually delete test users from Odoo UI:
   - Go to **Settings → Users & Companies → Users**
   - Search for "Test" users
   - Archive or delete them

### Delete Test User Records

Using Odoo shell:
```bash
docker-compose exec web python /odoo/odoo-bin shell -c /etc/odoo/odoo.conf -d odoo19
```

```python
# In shell:
test_users = env['res.users'].search([
    ('login', 'in', ['finance.manager', 'finance.officer', 'collection.staff', 'finance.all'])
])
test_users.unlink()
env.cr.commit()
exit()
```

---

## 📝 Notes

- **Password Security:** Test users have simple passwords (`test123`). Never use simple passwords in production!
- **noupdate Flag:** The XML file uses `noupdate="1"` which means test users won't be updated on module upgrade. This is intentional to preserve their state during testing.
- **Production Warning:** **ALWAYS remove test users before deploying to production!**
- **Multi-Company:** Test users are assigned to the main company. Modify `company_id` and `company_ids` for multi-company testing.

---

## 🎯 Summary

You now have three methods to create test users:
1. **XML Data File** - Best for team development
2. **Manual UI** - Best for one-time testing
3. **Python Script** - Best for quick custom setups

Choose the method that best fits your workflow and always remember to clean up before production deployment! 🚀
