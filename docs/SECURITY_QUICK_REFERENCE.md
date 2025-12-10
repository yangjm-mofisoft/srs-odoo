# Security Management Quick Reference

## Groups vs Roles vs Privileges - Visual Guide

### The Relationship

```
┌─────────────────────────────────────────────────────────┐
│                    ODOO SECURITY                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐         ┌──────────────┐               │
│  │   USERS    │  →→→→→  │    GROUPS    │               │
│  │            │         │   (Roles)    │               │
│  │ John Doe   │         │              │               │
│  │ Jane Smith │         │ ✓ Officer    │               │
│  │ Bob Lee    │         │ ✓ Manager    │               │
│  └────────────┘         │ ✓ Collection │               │
│                         └──────┬───────┘               │
│                                │                         │
│                                ↓                         │
│                    ┌────────────────────┐               │
│                    │  ACCESS RIGHTS     │               │
│                    │  (Privileges)      │               │
│                    │                    │               │
│                    │  Contract: CRUD    │               │
│                    │  Payment:  CR--    │               │
│                    │  Product:  R---    │               │
│                    └────────────────────┘               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## The 3 Security Layers

### Layer 1: Groups (Who you are)

```
┌──────────────────────────────────────┐
│         SECURITY GROUPS              │
│         (aka "Roles")                │
├──────────────────────────────────────┤
│                                      │
│  👤 Finance Officer                  │
│     - Basic operations               │
│     - Can't approve/delete           │
│                                      │
│  👔 Finance Manager                  │
│     - Full access                    │
│     - Can approve/delete             │
│                                      │
│  📞 Collection Staff                 │
│     - View overdue only              │
│     - Send reminders                 │
│                                      │
└──────────────────────────────────────┘
```

### Layer 2: Access Rights (What you can do)

```
┌─────────────────────────────────────────────────┐
│         ACCESS RIGHTS MATRIX                    │
│         (CRUD Permissions)                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  Model: finance.contract                       │
│  ┌──────────┬──────┬───────┬────────┬────────┐│
│  │ Group    │ Read │ Write │ Create │ Delete ││
│  ├──────────┼──────┼───────┼────────┼────────┤│
│  │ Officer  │  ✓   │   ✓   │   ✓    │   ✗   ││
│  │ Manager  │  ✓   │   ✓   │   ✓    │   ✓   ││
│  │ Collect  │  ✓   │   ✗   │   ✗    │   ✗   ││
│  └──────────┴──────┴───────┴────────┴────────┘│
│                                                 │
└─────────────────────────────────────────────────┘
```

### Layer 3: Record Rules (Which records)

```
┌──────────────────────────────────────────┐
│         RECORD RULES                     │
│         (Row-Level Security)             │
├──────────────────────────────────────────┤
│                                          │
│  Rule: Officer Own Contracts             │
│  Domain: [('user_id', '=', uid)]         │
│  → Officers see only their contracts     │
│                                          │
│  Rule: Collection Overdue Only           │
│  Domain: [('total_overdue_days', '>', 0)]│
│  → Collection sees only overdue          │
│                                          │
└──────────────────────────────────────────┘
```

---

## Code vs UI Management

### Where to Define Security

```
┌───────────────────────────────────────────────────────┐
│                 SECURITY DEFINITION                    │
├───────────────────────────────────────────────────────┤
│                                                        │
│  📁 CODE (Files)           💻 UI (Odoo Interface)     │
│  ═══════════════           ═══════════════════════    │
│                                                        │
│  security/security.xml     Settings → Users           │
│  ├─ Define Groups          ├─ Assign groups to users  │
│  └─ Base structure         └─ Manage users            │
│                                                        │
│  security/ir.model.        Asset Finance → Config     │
│    access.csv              → Security → Access Rights │
│  ├─ Base permissions       ├─ Modify CRUD permissions │
│  └─ Version controlled     ├─ Add new access rules    │
│                            └─ Quick adjustments       │
│                                                        │
│  ✅ Use for:               ✅ Use for:                 │
│  • Base security           • Custom adjustments       │
│  • Deployment              • Quick fixes              │
│  • Version control         • Company-specific rules   │
│  • Multi-instance          • Testing permissions      │
│                                                        │
└───────────────────────────────────────────────────────┘
```

---

## NEW: UI-Based Security Management

### Menu Navigation

```
Asset Finance
└── Configuration
    └── Security  ⬅️ NEW!
        ├── Access Rights     (Manage CRUD permissions)
        ├── User Roles        (Manage groups)
        └── Record Rules      (Row-level filtering)
```

### Access Rights Screen

```
┌─────────────────────────────────────────────────────────┐
│  Asset Finance → Configuration → Security → Access Rights│
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [Create]  [Import]  [Export]  ⚙️                       │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Name                    Model        Group   R W C D│ │
│  ├────────────────────────────────────────────────────┤ │
│  │ access.contract.officer Contract  Officer ✓ ✓ ✓ ✗│ │
│  │ access.contract.manager Contract  Manager ✓ ✓ ✓ ✓│ │
│  │ access.payment.officer  Payment   Officer ✓ ✓ ✓ ✗│ │
│  │ access.product.manager  Product   Manager ✓ ✓ ✓ ✓│ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  💡 Tip: Changes take effect immediately!               │
│      No module upgrade required.                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Common Tasks

### Task 1: Grant New Permission

**Scenario**: Allow Finance Officers to delete contracts

**Via UI** (Recommended for quick changes):
```
1. Asset Finance → Configuration → Security → Access Rights
2. Find: access.contract.officer
3. Check [✓] Delete column
4. Save
5. ✅ Done! (No restart needed)
```

**Via Code** (Recommended for permanent changes):
```
1. Edit: security/ir.model.access.csv
2. Change: ...,1,1,1,0  →  ...,1,1,1,1
                    ↑ Delete permission
3. Upgrade module
4. ✅ Done!
```

---

### Task 2: Create New Role

**Scenario**: Create "Finance Analyst" (read-only role)

**Via UI**:
```
Step 1: Create Group
========================================
1. Asset Finance → Configuration → Security → User Roles
2. Click [Create]
3. Fill in:
   Name: Finance Analyst
   Category: Asset Finance
4. Save

Step 2: Create Access Rights
========================================
1. Asset Finance → Configuration → Security → Access Rights
2. Click [Create] for each model:

   For Contracts:
   - Name: access.contract.analyst
   - Model: finance.contract
   - Group: Finance Analyst
   - Read: ✓
   - Write: ✗
   - Create: ✗
   - Delete: ✗

   Repeat for other models...

3. ✅ Done!
```

---

### Task 3: Assign Role to User

**Via UI** (Only way to do this):
```
1. Settings → Users → [Select User]
2. Access Rights tab
3. Asset Finance section:
   [✓] Finance Analyst  ⬅️ Check this
4. Save
5. User must logout/login
6. ✅ Done!
```

---

## Comparison Matrix

### Code vs UI - When to Use What

| Aspect | Code (CSV/XML) | UI (Access Rights Menu) |
|--------|----------------|-------------------------|
| **Speed** | Slow (requires deploy) | Fast (immediate) |
| **Version Control** | ✅ Yes (Git) | ❌ No |
| **Multi-Instance** | ✅ Easy (deploy once) | ❌ Hard (manual each) |
| **Quick Fix** | ❌ Requires developer | ✅ Admin can do it |
| **Audit Trail** | ✅ Git history | ⚠️ Odoo audit log |
| **Rollback** | ✅ Easy (Git revert) | ⚠️ Manual undo |
| **Documentation** | ✅ Self-documenting | ❌ Need external docs |
| **Testing** | ✅ Dev → Staging → Prod | ⚠️ Test in production |

**Recommendation**:
- **Base permissions** → Code (CSV)
- **Customizations** → UI (Access Rights menu)

---

## Permission Inheritance

### How Groups Inherit Permissions

```
┌──────────────────────────────────────────┐
│     GROUP INHERITANCE                     │
├──────────────────────────────────────────┤
│                                          │
│  User: John Doe                          │
│  Groups: Finance Officer + Manager       │
│                                          │
│  Permissions: OR logic                   │
│  ┌────────────────┬────────┬──────────┐ │
│  │ Action         │ Officer│ Manager  │ │
│  ├────────────────┼────────┼──────────┤ │
│  │ Delete Contract│   ✗    │    ✓     │ │
│  │ Result         │        │    ✓     │ │
│  └────────────────┴────────┴──────────┘ │
│                                          │
│  ✅ If ANY group allows → User can do it│
│                                          │
└──────────────────────────────────────────┘
```

---

## Terminology Cheat Sheet

| Odoo Term | Business Term | Example |
|-----------|--------------|---------|
| **Security Group** | Role | Finance Officer |
| **Access Rights** | Privileges | Can create contracts |
| **Record Rules** | Data filters | See only own records |
| **CRUD** | Permissions | Create, Read, Update, Delete |
| **ir.model.access** | Access control | Permission table |
| **res.groups** | User groups | Role definitions |

---

## Quick Decision Tree

```
Need to change permissions?
│
├─ Is it a permanent change for all instances?
│  └─ YES → Use Code (CSV)
│     └─ Edit ir.model.access.csv → Upgrade module
│
├─ Is it a temporary or company-specific change?
│  └─ YES → Use UI (Access Rights Menu)
│     └─ Asset Finance → Config → Security → Access Rights
│
├─ Need to create a new role?
│  └─ BOTH → Group in Code, Permissions in UI
│     └─ 1. Add group in security.xml
│     └─ 2. Add permissions in UI or CSV
│
└─ Need to assign role to user?
   └─ ALWAYS UI → Settings → Users → Access Rights tab
```

---

## Summary

### ✅ What You Can Now Do

1. **View** all access rights via UI
   - Asset Finance → Configuration → Security → Access Rights

2. **Modify** permissions without code
   - Click any row → Edit → Save

3. **Create** new access rules
   - Click Create → Fill form → Save

4. **Manage** roles visually
   - Asset Finance → Configuration → Security → User Roles

5. **Immediate** changes
   - No module upgrade needed
   - User just needs to logout/login

### 🎯 Best Practices

1. **Keep base permissions in code** (CSV)
2. **Allow UI customizations** for edge cases
3. **Document changes** made via UI
4. **Test permissions** after changes
5. **Regular security audits** (quarterly)

### 📚 Related Guides

- [SECURITY_MANAGEMENT_GUIDE.md](SECURITY_MANAGEMENT_GUIDE.md) - Full guide
- [USER_MANAGEMENT_GUIDE.md](USER_MANAGEMENT_GUIDE.md) - User setup
- [USER_ROLES_QUICK_REFERENCE.md](USER_ROLES_QUICK_REFERENCE.md) - Role comparison

---

**Version**: 1.0
**Updated**: 2025-12-10
