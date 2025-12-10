# Troubleshooting: "Asset Finance Menu Opens Discussion Page"

## Problem
When clicking on "Asset Finance" menu, it redirects to the Discussion (Discuss) page instead of showing the Asset Finance module.

## Root Cause
This happens when a user has Administrator rights but lacks the proper Asset Finance application groups.

---

## Solution: Check User Configuration

### Step 1: Verify User Has Asset Finance Groups

1. Go to: **Settings → Users & Companies → Users**
2. Find and open the user (e.g., "Administrator")
3. Go to **Access Rights** tab
4. Scroll down to **Asset Finance** section
5. Verify at least ONE of these is checked:
   - ☑️ **Finance Officer**
   - ☑️ **Finance Manager**
   - ☑️ **Collection Staff**

### Step 2: Check Application Access (IMPORTANT!)

Still in the Access Rights tab, scroll to **Administration** section:

**For Administrator users**, make sure you have:
- ☑️ **Settings** (Administration / Settings)
- ☑️ **Access Rights** (Administration / Access Rights)

**Additionally, verify Other section**:
- ☑️ **Internal User** (should already be checked)

### Step 3: Clear User Session

After making changes:
1. **Save** the user record
2. Have the user **logout completely**
3. **Close all browser tabs**
4. **Clear browser cache** (Ctrl+Shift+Delete)
5. **Login again**

---

## Common Scenarios

### Scenario 1: Administrator Can't Access Asset Finance

**Symptoms**:
- User is Administrator
- Has Finance Manager checked
- Still redirects to Discuss

**Solution**:
```
1. Settings → Users → [Admin User]
2. Access Rights tab
3. Verify:
   Asset Finance:
   ☑️ Finance Manager

   Administration:
   ☑️ Settings
   ☑️ Access Rights

   Other:
   ☑️ Internal User
4. Save
5. Logout/Login
```

### Scenario 2: Regular User Can't See Menu

**Symptoms**:
- User doesn't see "Asset Finance" in main menu at all

**Solution**:
- User needs at least ONE Asset Finance group:
  - Finance Officer, OR
  - Finance Manager, OR
  - Collection Staff

### Scenario 3: Menu Exists But Shows Empty Page

**Symptoms**:
- Can see Asset Finance menu
- Clicking it shows blank page or "No records found"

**Possible causes**:
1. **No dashboard configured** - Check if dashboard module is installed
2. **No contracts exist** - Create a test contract
3. **Record rules blocking** - Check if Collection Staff trying to access (they can only see active/repo)

---

## Verification Checklist

After configuring the user, verify they can:

### For Finance Officer:
- [ ] See "Asset Finance" menu in main navigation
- [ ] Click "Asset Finance" → Opens Dashboard
- [ ] Navigate to "Operations" → "Contracts"
- [ ] Click "Create" button (should work)
- [ ] Try to delete a contract (should fail - expected)

### For Finance Manager:
- [ ] All Finance Officer capabilities
- [ ] Can delete contracts
- [ ] Can access Configuration menu
- [ ] Can see Settings submenu

### For Collection Staff:
- [ ] See "Asset Finance" menu
- [ ] Can view active contracts (with overdue filter)
- [ ] Cannot create new contracts (Create button hidden)
- [ ] Cannot see draft contracts

---

## Technical Details

### Why This Happens

Odoo's menu system works as follows:

1. **Menu Visibility**: Determined by `groups` attribute in XML
   ```xml
   <menuitem id="menu_finance_root"
             name="Asset Finance"
             groups="group_finance_officer,group_finance_manager,group_collection_staff"/>
   ```

2. **Default Action**: Each menu has a default action
   - If user lacks permissions for the action → redirects to Discuss
   - If action not defined → shows blank page

3. **Group Inheritance**:
   ```
   Finance Manager
   └── Inherits from Finance Officer
       └── Inherits from base.group_user
   ```

### Module Category

The groups are now organized under **"Asset Finance"** category:

```xml
<record id="module_category_asset_finance" model="ir.module.category">
    <field name="name">Asset Finance</field>
</record>

<record id="group_finance_manager" model="res.groups">
    <field name="name">Finance Manager</field>
    <field name="category_id" ref="module_category_asset_finance"/>
</record>
```

This makes them appear properly in the Access Rights tab.

---

## Quick Fixes

### Fix 1: Reset User Permissions

If a user is completely broken:

1. Remove ALL Asset Finance groups
2. Save
3. Re-add Finance Manager group
4. Save
5. Logout/Login

### Fix 2: Create Test User

To verify the module works:

```python
# Via Odoo shell (docker exec)
new_user = env['res.users'].create({
    'name': 'Test Manager',
    'login': 'test.manager@company.com',
    'groups_id': [(6, 0, [
        env.ref('base.group_user').id,
        env.ref('asset_finance.group_finance_manager').id,
    ])]
})
```

Login as `test.manager@company.com` to verify.

### Fix 3: Check Menu XML

Verify menu is properly defined:

```bash
# Search for menu definition
grep -r "menu_finance_root" custom_addons/asset_finance/views/
```

Should return:
```xml
<menuitem id="menu_finance_root"
          name="Asset Finance"
          sequence="10"/>
```

---

## Database Issues

### If Module Won't Upgrade

```bash
# Force upgrade
docker-compose run --rm web -d vfs -u asset_finance --stop-after-init

# If that fails, try reinstalling
docker-compose run --rm web -d vfs --init asset_finance --stop-after-init
```

### Check Group Exists in Database

```sql
-- Connect to database
docker exec -it odoo-dev-db-1 psql -U odoo -d vfs

-- Verify groups exist
SELECT id, name, category_id
FROM res_groups
WHERE name LIKE 'Finance%';

-- Should show:
--  id | name              | category_id
-- ----+-------------------+-------------
--   X | Finance Officer   | Y
--   X | Finance Manager   | Y
--   X | Collection Staff  | Y
```

---

## Still Not Working?

### Check Logs

```bash
# View Odoo logs
docker-compose logs -f web

# Look for errors like:
# - Access Denied
# - Missing group
# - Menu not found
```

### Enable Debug Mode

1. Add `?debug=1` to URL:
   ```
   http://localhost:8069/web?debug=1
   ```

2. Check browser console (F12) for JavaScript errors

3. Go to Settings → Technical → User Interface → Menu Items
   - Search for "Asset Finance"
   - Check if it exists
   - Check Groups field

### Verify Module Installed

```
Settings → Apps → Search "Asset Finance"
Should show: ✅ Installed
```

If not installed → Click Install

---

## Prevention

### When Creating New Users

Always follow this checklist:

1. **Basic Info**:
   - Name
   - Email
   - Password

2. **Access Rights** (minimum required):
   ```
   Other:
   ☑️ Internal User

   Asset Finance:
   ☑️ [Choose appropriate role]
   ```

3. **Save** and test immediately

4. Have user **logout/login** after any permission changes

---

## Summary

### Most Common Issue
✅ **Administrator users need BOTH**:
- Administration / Settings access
- Asset Finance / [Role] access

### Quick Test
1. Can you see "Asset Finance" in main menu? → Groups assigned
2. Clicking it shows Dashboard? → Permissions correct
3. Can create records? → Access rights working

If answer is NO to any → Follow the solutions above

---

**Document Version**: 1.0
**Last Updated**: 2025-12-10
**Module**: Asset Financing Management
