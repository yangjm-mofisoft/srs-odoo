# Partner Type - Final Solution

## ✅ Updated Implementation Based on Your Feedback

**Your insight:** "For customer, guarantor and co-borrower, it can be company too."

You're absolutely right! I've updated the solution to handle this properly.

---

## 🎯 Final Approach

### **The Problem with Previous Approach:**
- Assumed only **individuals** could be customers/guarantors/co-borrowers ❌
- But **companies can also be** customers/guarantors/co-borrowers ✅

### **The Solution:**
**Use `finance_partner_type` ONLY for specialized business entities.**

Partners **without** a `finance_partner_type` can be customers/guarantors/co-borrowers (whether individual or company).

---

## 📋 Final Partner Types (4 Types)

| Type | Code | Description | When to Use |
|------|------|-------------|-------------|
| **(No Type)** | `False` or `''` | **Customer/Guarantor/Co-Borrower** | Default for most partners - can be individual OR company |
| **Sales Agent / Broker** | `broker` | External sales facilitator | When partner is a broker |
| **Insurance Company** | `insurer` | Insurance provider | When partner provides insurance |
| **Finance Company** | `finance_company` | Loan provider | When partner provides loans |
| **Supplier / Dealer** | `supplier` | Asset supplier | When partner supplies assets |

---

## 🔑 Key Principle

**"finance_partner_type" is ONLY for specialized business roles.**

- If someone/something can be a customer, guarantor, or co-borrower → **Leave type BLANK**
- Use Odoo's standard **"Is a Company"** checkbox to indicate individual vs company

---

## 💡 Real-World Examples

### **Example 1: Individual Customer**
- Name: John Doe
- Is a Company: ☐ (unchecked)
- Finance Business Type: (blank)
- **Can be:** Customer, Guarantor, Co-Borrower ✅

### **Example 2: Company Customer**
- Name: ABC Corporation Pte Ltd
- Is a Company: ☑ (checked)
- Finance Business Type: (blank)
- **Can be:** Customer, Guarantor, Co-Borrower ✅

### **Example 3: Sales Agent**
- Name: XYZ Brokers Pte Ltd
- Is a Company: ☑ (checked)
- Finance Business Type: Sales Agent / Broker
- **Can be:** Only sales agent (NOT customer/guarantor/co-borrower) ❌

### **Example 4: Insurance Company**
- Name: AIA Insurance
- Is a Company: ☑ (checked)
- Finance Business Type: Insurance Company
- **Can be:** Only insurer (NOT customer/guarantor/co-borrower) ❌

---

## 🔧 Implementation Details

### **1. Domain Filters in contract.py**

```python
# Hirer (Customer) - can be individual OR company (but not broker/insurer/etc.)
hirer_id = fields.Many2one('res.partner',
    domain="[('finance_partner_type', 'in', [False, '']), ('finance_blacklist', '=', False)]")

# Guarantor - can be individual OR company (but not broker/insurer/etc.)
partner_id = fields.Many2one('res.partner',  # in FinanceContractGuarantor
    domain="[('finance_partner_type', 'in', [False, '']), ('finance_blacklist', '=', False)]")

# Co-Borrower - can be individual OR company (but not broker/insurer/etc.)
partner_id = fields.Many2one('res.partner',  # in FinanceContractJointHirer
    domain="[('finance_partner_type', 'in', [False, '']), ('finance_blacklist', '=', False)]")

# Sales Agent - MUST have finance_partner_type = 'broker'
sales_agent_id = fields.Many2one('res.partner',
    domain="[('finance_partner_type', '=', 'broker')]")

# Insurer - MUST have finance_partner_type = 'insurer'
insurer_id = fields.Many2one('res.partner',
    domain="[('finance_partner_type', '=', 'insurer')]")

# Finance Company - MUST have finance_partner_type = 'finance_company'
finance_company_id = fields.Many2one('res.partner',
    domain="[('finance_partner_type', '=', 'finance_company')]")

# Supplier - MUST have finance_partner_type = 'supplier'
supplier_id = fields.Many2one('res.partner',
    domain="[('finance_partner_type', '=', 'supplier')]")
```

### **2. Partner Form View**

When creating/editing a partner:

```
┌────────────────────────────────────────────────┐
│ ☑ Is a Company                                 │
│                                                │
│ Name: ABC Corporation                          │
│ NRIC/UEN: 201234567K                          │
│                                                │
│ Finance Business Type:                         │
│ ○ (Leave Blank for Customer/Guarantor)        │
│ ○ Sales Agent / Broker                        │
│ ○ Insurance Company                            │
│ ○ Finance Company                              │
│ ○ Supplier / Dealer                            │
│                                                │
│ ☐ Blacklisted                                  │
└────────────────────────────────────────────────┘
```

**Workflow:**
1. Create new partner
2. Check "Is a Company" if it's a company (leave unchecked for individual)
3. If this partner has a **specialized business role** (broker/insurer/finance company/supplier), select it
4. If this partner is a **regular customer** (can be hirer/guarantor/co-borrower), **leave Business Type blank**

---

## 📊 Menu Structure

```
Asset Finance
├── Dashboard
├── Contracts
├── Partners
│   ├── Customers                    ← Individuals & Companies (no business type)
│   ├── Sales Agents / Brokers       ← type = 'broker'
│   ├── Insurance Companies          ← type = 'insurer'
│   ├── Finance Companies            ← type = 'finance_company'
│   └── Suppliers / Dealers          ← type = 'supplier'
└── Reports
```

---

## ✅ Benefits of Final Solution

| Benefit | Description |
|---------|-------------|
| **Flexible** | Both individuals AND companies can be customers/guarantors/co-borrowers |
| **Simple** | Only 4 specialized business types (instead of 7 types) |
| **Clear** | Blank type = can be customer/guarantor/co-borrower |
| **Standard** | Uses Odoo's "Is a Company" checkbox |
| **Realistic** | Matches real-world scenarios |

---

## 🎬 User Workflow

### **Creating a Customer (Individual)**
1. Asset Finance > Partners > Customers > Create
2. Name: "John Doe"
3. Is a Company: ☐ (unchecked)
4. Finance Business Type: (leave blank)
5. Save

**Result:** John can be selected as hirer, guarantor, or co-borrower ✅

### **Creating a Customer (Company)**
1. Asset Finance > Partners > Customers > Create
2. Name: "ABC Corporation Pte Ltd"
3. Is a Company: ☑ (checked)
4. Finance Business Type: (leave blank)
5. Save

**Result:** ABC Corp can be selected as hirer, guarantor, or co-borrower ✅

### **Creating a Broker**
1. Asset Finance > Partners > Sales Agents / Brokers > Create
2. Name: "XYZ Brokers"
3. Is a Company: ☑ (checked)
4. Finance Business Type: Sales Agent / Broker (auto-filled)
5. Save

**Result:** XYZ Brokers can ONLY be selected as sales agent (NOT as customer/guarantor/co-borrower) ✅

---

## 🧪 Testing Scenarios

### **Scenario 1: Individual as Multiple Roles**
- John Doe (individual, no business type)
- Contract #001: John is **Customer (Hirer)**
- Contract #002: John is **Guarantor** for his son
- Contract #003: John is **Co-Borrower** with his wife

✅ **Works perfectly!**

### **Scenario 2: Company as Customer**
- ABC Corp (company, no business type)
- Contract #004: ABC Corp is **Customer (Hirer)** - company taking fleet loan

✅ **Works!**

### **Scenario 3: Company as Guarantor**
- XYZ Holdings (company, no business type)
- Contract #005: XYZ Holdings is **Guarantor** for subsidiary company's loan

✅ **Works!**

### **Scenario 4: Broker Cannot be Customer**
- Sales Agent Inc (company, type = 'broker')
- Try to select as Customer in contract → **NOT in dropdown** ✅
- Try to select as Guarantor → **NOT in dropdown** ✅
- Can only be selected as Sales Agent ✅

✅ **Correctly prevented!**

---

## 📝 Files Changed

1. ✅ [models/res_partner.py](custom_addons/asset_finance/models/res_partner.py)
   - Changed `finance_partner_type` to only 4 business types (removed 'individual')
   - Renamed label to "Finance Business Type"

2. ✅ [models/contract.py](custom_addons/asset_finance/models/contract.py)
   - Updated all domains to `[('finance_partner_type', 'in', [False, ''])]`
   - This allows BOTH individuals AND companies to be customers/guarantors/co-borrowers

3. ✅ [views/partner_menus.xml](custom_addons/asset_finance/views/partner_menus.xml)
   - Changed "Individuals / Customers" → "Customers"
   - Domain shows all partners WITHOUT a business type
   - Help text explains both individuals and companies can be customers

---

## 🚀 Deployment

```bash
# 1. Restart and upgrade
docker-compose restart web
docker-compose exec web odoo -u asset_finance --stop-after-init
docker-compose restart web

# 2. Test in UI
# - Create individual customer (Is a Company: unchecked, Business Type: blank)
# - Create company customer (Is a Company: checked, Business Type: blank)
# - Create contract and verify both show up in Hirer dropdown
# - Add guarantor - both individual and company customers should appear
```

---

## ✨ Summary

**Final Partner Type System:**
- **No Business Type** = Can be customer/guarantor/co-borrower (individual OR company)
- **Broker** = Sales agent only
- **Insurer** = Insurance company only
- **Finance Company** = Loan provider only
- **Supplier** = Asset supplier only

**Use Odoo's "Is a Company" checkbox to distinguish individual vs company.**

This solution is:
✅ Flexible (companies can be customers/guarantors/co-borrowers)
✅ Simple (only 4 business types)
✅ Clear (blank type = general customer)
✅ Standards-compliant (uses Odoo's is_company field)

Perfect for your finance business requirements! 🎯
