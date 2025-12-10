# Quick Start Testing Guide - Asset Finance Module

## ⚡ 10-Minute Setup

### Step 1: Create Test Users (5 minutes)

**Navigate to:** Settings → Users & Companies → Users → Create

#### User 1: Finance Officer
```
Name: Test Finance Officer
Email: finance.officer@test.com
Password: test123
Group: Asset Financing → Finance Officer
Extra: Accounting → Billing, Sales → User
```

#### User 2: Finance Manager
```
Name: Test Finance Manager
Email: finance.manager@test.com
Password: manager123
Group: Asset Financing → Finance Manager
Extra: Accounting → Accountant, Administration → Settings
```

#### User 3: Collection Staff
```
Name: Test Collection Staff
Email: collection.staff@test.com
Password: collect123
Group: Asset Financing → Collection Staff
```

---

### Step 2: Create Sample Data (5 minutes)

#### Customer
```
Navigate: Contacts → Create
Name: John Doe Test
Email: john.doe@test.com
Phone: +65 1234 5678
Customer Type: Individual
☑ Is Finance Customer
```

#### Vehicle
```
Navigate: Fleet → Vehicles → Create
License Plate: SXX1234A
Model: Create new → Brand: Toyota, Model: Corolla
Year: 2023
```

#### Financial Product
```
Navigate: Asset Finance → Configuration → Financial Products
Use existing or verify one exists
```

---

### Step 3: Quick Permission Test (2 minutes each role)

#### Test Finance Officer
```bash
Login: finance.officer@test.com / test123

✅ Try: Create Contract → Should WORK
❌ Try: Approve Contract → Should FAIL (button hidden)
✅ Try: Edit Draft Contract → Should WORK
❌ Try: Delete Contract → Should FAIL
```

#### Test Finance Manager
```bash
Login: finance.manager@test.com / manager123

✅ Try: Approve Contract → Should WORK
✅ Try: Disburse Funds → Should WORK
✅ Try: Access Settings → Should WORK
✅ Try: Delete Contract → Should WORK
```

#### Test Collection Staff
```bash
Login: collection.staff@test.com / collect123

✅ Try: View Active Contracts → Should WORK
✅ Try: Send Reminder → Should WORK
❌ Try: View Draft Contracts → Should FAIL (not visible)
❌ Try: Create Contract → Should FAIL (button hidden)
```

---

## 🎯 Essential Tests (30 seconds each)

### Contract Lifecycle Test
1. **Officer**: Create contract → Save as Draft ✅
2. **Manager**: Open draft → Approve ✅
3. **Manager**: Click Disburse → Complete wizard ✅
4. **Collection**: Send Payment Reminder ✅

### Permission Boundary Test
1. **Officer**: Try to approve → ❌ Should fail
2. **Collection**: Try to create → ❌ Should fail
3. **Collection**: Try to edit → ❌ Should fail

---

## 🔍 Quick Verification Checklist

### Finance Officer ✅
- [ ] Can login
- [ ] Can see "Create" button
- [ ] Cannot see "Approve" button
- [ ] Can generate schedule

### Finance Manager ✅
- [ ] Can login
- [ ] Can approve contracts
- [ ] Can disburse funds
- [ ] Can access Settings menu

### Collection Staff ✅
- [ ] Can login
- [ ] Only sees active/repo contracts
- [ ] Can send emails
- [ ] Cannot create/approve

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Menu not visible | Logout → Login again |
| Button missing | Check user group assignment |
| Access denied | Expected for wrong role - correct! |
| Email not sending | Configure SMTP in Settings |

---

## 📊 Test Account Summary

| Role | Login | Key Test |
|------|-------|----------|
| Officer | `finance.officer@test.com` | Create but can't approve |
| Manager | `finance.manager@test.com` | Can do everything |
| Collection | `collection.staff@test.com` | View only active, send emails |

---

## ⚠️ Important Notes

- **Test passwords** are simple for testing only
- **Delete test accounts** before production
- **Logout/Login** required after group changes
- See full guide: `TESTING_ACCOUNTS_GUIDE.md`

---

**Setup Time**: ~10 minutes
**Test Time**: ~5 minutes per role
**Total**: ~25 minutes for complete testing

---

✅ **Done? Your Asset Finance module is ready for production!**
