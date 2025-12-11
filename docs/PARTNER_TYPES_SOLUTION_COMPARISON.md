# Partner Types: Boolean Fields vs Selection Field Comparison

## 🎯 The Question

**Should we use:**
- **Option A:** Multiple boolean fields (`is_finance_customer`, `is_finance_broker`, etc.)
- **Option B:** Single selection field (`finance_partner_type`)

---

## 📊 Detailed Comparison

### **Option A: Multiple Boolean Fields** (Currently Recommended)

```python
# In res_partner.py
is_finance_customer = fields.Boolean(string="Is Finance Customer")
is_finance_guarantor = fields.Boolean(string="Is Guarantor")
is_finance_broker = fields.Boolean(string="Is Broker")
is_finance_joint_hirer = fields.Boolean(string="Is Co-Borrower")
is_insurer = fields.Boolean(string="Is Insurance Company")
is_finance_company = fields.Boolean(string="Is Finance Company")
```

**Advantages:**
- ✅ **Partners can have multiple roles** (e.g., someone can be both a Customer AND a Guarantor)
- ✅ **Flexible** - Easy to add/remove roles without affecting existing data
- ✅ **Simple queries** - Direct field access
- ✅ **No data migration** - 3 fields already exist
- ✅ **Independent filtering** - Can filter by multiple types simultaneously

**Disadvantages:**
- ❌ **Many fields** - 6 boolean fields clutters the model
- ❌ **UI clutter** - 6 checkboxes on partner form
- ❌ **No mutual exclusivity** - Can't enforce "pick only one" if needed
- ❌ **Database space** - 6 columns instead of 1

---

### **Option B: Single Selection Field** ⭐ **BETTER CHOICE**

```python
# In res_partner.py
finance_partner_type = fields.Selection([
    ('customer', 'Finance Customer (Hirer)'),
    ('guarantor', 'Guarantor'),
    ('co_borrower', 'Co-Borrower'),
    ('broker', 'Sales Agent / Broker'),
    ('insurer', 'Insurance Company'),
    ('finance_company', 'Finance Company'),
    ('supplier', 'Supplier / Dealer'),
], string="Finance Partner Type", help="Primary role of this partner in finance operations")
```

**Advantages:**
- ✅ **Cleaner model** - Only 1 field instead of 6
- ✅ **Cleaner UI** - Single dropdown/radio selection
- ✅ **Better data integrity** - Clear primary role
- ✅ **Simpler domains** - `domain="[('finance_partner_type', '=', 'customer')]"`
- ✅ **Better reporting** - Easy to count partners by type
- ✅ **Less storage** - 1 column vs 6 columns
- ✅ **Standard Odoo pattern** - Many Odoo models use this approach

**Disadvantages:**
- ❌ **Single role only** - Partner can't be both Customer AND Guarantor
- ❌ **Requires data migration** - Need to convert existing boolean flags
- ❌ **Less flexible** - Can't easily represent multiple roles

---

## 🤔 Which Should You Choose?

### **Key Question: Can a partner have multiple finance roles?**

#### **If NO (partner has ONE primary role):**
→ **Use Selection Field (Option B)** ⭐ **RECOMMENDED**

**Real-world scenarios:**
- ✅ A person is EITHER a Customer OR a Guarantor (not both)
- ✅ A company is EITHER a Finance Company OR a Supplier (not both)
- ✅ Each partner has ONE clear primary role

#### **If YES (partner can have multiple roles):**
→ **Use Boolean Fields (Option A)** or **Use Many2many Tags**

**Real-world scenarios:**
- ❌ A customer might also guarantee someone else's loan
- ❌ A broker might also be a customer
- ❌ A supplier might also provide insurance

---

## 💡 HYBRID SOLUTION (Best of Both Worlds)

Use **ONE selection field for PRIMARY role** + **Tags for additional roles**:

```python
# In res_partner.py

# PRIMARY role (mutually exclusive)
finance_partner_type = fields.Selection([
    ('customer', 'Customer (Hirer)'),
    ('guarantor', 'Guarantor'),
    ('co_borrower', 'Co-Borrower'),
    ('broker', 'Sales Agent / Broker'),
    ('insurer', 'Insurance Company'),
    ('finance_company', 'Finance Company'),
    ('supplier', 'Supplier / Dealer'),
], string="Finance Partner Type",
   help="Primary role of this partner in finance operations")

# ADDITIONAL roles (can have multiple)
finance_role_ids = fields.Many2many(
    'finance.partner.role',
    string="Additional Finance Roles",
    help="Additional roles this partner can fulfill"
)
```

Then create a simple model for roles:

```python
# In models/finance_partner_role.py
class FinancePartnerRole(models.Model):
    _name = 'finance.partner.role'
    _description = 'Finance Partner Additional Roles'

    name = fields.Char(string="Role Name", required=True)
    code = fields.Char(string="Code", required=True)
```

**This gives you:**
- ✅ Clear primary role (Selection field)
- ✅ Multiple additional roles (Many2many tags)
- ✅ Clean UI with both dropdown and tag badges
- ✅ Flexible for complex scenarios

---

## 🎯 RECOMMENDED SOLUTION: Single Selection Field

Based on typical finance business logic, I recommend **Option B: Single Selection Field**.

### **Rationale:**

1. **Clear Business Logic**
   - In finance, each partner typically has ONE primary role
   - A hirer is not usually a guarantor (conflict of interest)
   - A supplier is not also a finance company
   - Clear roles = better compliance and reporting

2. **Simpler Implementation**
   - Fewer fields to maintain
   - Cleaner code
   - Better performance

3. **Better User Experience**
   - Users see one clear "Partner Type" field
   - No confusion about checking multiple boxes
   - Easy to filter/search by type

4. **Standard Practice**
   - Odoo uses this pattern in many places (partner type, product type, etc.)
   - Familiar to Odoo users

---

## 🚀 IMPLEMENTATION: Single Selection Field

### Step 1: Update res_partner.py

```python
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # --- Identity ---
    nric = fields.Char(string="NRIC / FIN / UEN", help="National ID or Company Reg No")
    date_of_birth = fields.Date(string="Date of Birth / Incorporation")

    # --- Finance Partner Type (SINGLE FIELD) ---
    finance_partner_type = fields.Selection([
        ('customer', 'Finance Customer (Hirer)'),
        ('guarantor', 'Guarantor'),
        ('co_borrower', 'Co-Borrower / Joint Hirer'),
        ('broker', 'Sales Agent / Broker'),
        ('insurer', 'Insurance Company'),
        ('finance_company', 'Finance Company'),
        ('supplier', 'Supplier / Dealer'),
    ], string="Finance Partner Type",
       tracking=True,
       help="Primary role of this partner in finance operations")

    # --- Risk Management ---
    finance_blacklist = fields.Boolean(string="Blacklisted (Finance)")
    finance_blacklist_reason = fields.Char(string="Blacklist Reason")

    # Odoo has a standard 'type' field (Invoice, Delivery, Other).
    # We add a specific classification for your Finance needs.
    address_category = fields.Selection([
        ('residential', 'Residential'),
        ('work', 'Work / Office'),
        ('registered', 'Registered Address'),
        ('mailing', 'Mailing Address'),
        ('previous', 'Previous Address')
    ], string="Address Category")

    # Multiple Contact Numbers
    phone_ids = fields.One2many('res.partner.phone', 'partner_id', string="Contact Numbers")

    # REMOVE the old boolean fields:
    # is_finance_guarantor = fields.Boolean(...)  # DELETE
    # is_finance_broker = fields.Boolean(...)      # DELETE
    # is_finance_joint_hirer = fields.Boolean(...) # DELETE
```

### Step 2: Update contract.py Domain Filters

```python
# In models/contract.py

class FinanceContractGuarantor(models.Model):
    _name = 'finance.contract.guarantor'

    partner_id = fields.Many2one(
        'res.partner',
        string="Guarantor Name",
        required=True,
        domain="[('finance_partner_type', '=', 'guarantor'), ('finance_blacklist', '=', False)]",
        help="Individual or entity guaranteeing this contract."
    )

class FinanceContractJointHirer(models.Model):
    _name = 'finance.contract.joint.hirer'

    partner_id = fields.Many2one(
        'res.partner',
        string="Co-Borrower Name",
        required=True,
        domain="[('finance_partner_type', '=', 'co_borrower'), ('finance_blacklist', '=', False)]",
        help="Joint hirer sharing liability for this contract."
    )

class FinanceContract(models.Model):
    _name = 'finance.contract'

    # HIRER
    hirer_id = fields.Many2one(
        'res.partner',
        string="Hirer's Name",
        required=True,
        tracking=True,
        domain="[('finance_partner_type', '=', 'customer'), ('finance_blacklist', '=', False)]"
    )

    # SALES AGENT
    sales_agent_id = fields.Many2one(
        'res.partner',
        string="Salesperson (Agent)",
        domain="[('finance_partner_type', '=', 'broker'), ('active', '=', True)]",
        help="The external salesperson or broker associated with this deal."
    )

    # INSURER
    insurer_id = fields.Many2one(
        'res.partner',
        string="Insurer",
        domain="[('finance_partner_type', '=', 'insurer')]"
    )

    # FINANCE COMPANY
    finance_company_id = fields.Many2one(
        'res.partner',
        string="Finance Name",
        domain="[('finance_partner_type', '=', 'finance_company')]"
    )

    # SUPPLIER
    supplier_id = fields.Many2one(
        'res.partner',
        string="Supplier / Dealer",
        domain="[('finance_partner_type', '=', 'supplier')]"
    )
```

### Step 3: Update Partner Form View

```xml
<!-- In views/res_partner_views.xml -->
<record id="view_partner_form_finance_type" model="ir.ui.view">
    <field name="name">res.partner.form.finance.type</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_partner_form"/>
    <field name="arch" type="xml">
        <!-- Add Finance Type after company field -->
        <xpath expr="//field[@name='company_id']" position="after">
            <field name="finance_partner_type"
                   widget="badge"
                   decoration-info="finance_partner_type == 'customer'"
                   decoration-success="finance_partner_type == 'broker'"
                   decoration-warning="finance_partner_type == 'guarantor'"
                   decoration-primary="finance_partner_type == 'finance_company'"/>
        </xpath>

        <!-- Show blacklist warning if needed -->
        <xpath expr="//field[@name='finance_partner_type']" position="after">
            <field name="finance_blacklist" widget="boolean_toggle"/>
            <field name="finance_blacklist_reason"
                   invisible="not finance_blacklist"
                   placeholder="Reason for blacklisting..."/>
        </xpath>
    </field>
</record>
```

### Step 4: Create Partner Menus (Same as before)

```xml
<!-- In views/partner_menus.xml -->
<odoo>
    <!-- ACTION: Customers -->
    <record id="action_finance_customers" model="ir.actions.act_window">
        <field name="name">Customers (Hirers)</field>
        <field name="res_model">res.partner</field>
        <field name="view_mode">list,form</field>
        <field name="domain">[('finance_partner_type', '=', 'customer')]</field>
        <field name="context">{
            'default_finance_partner_type': 'customer',
            'default_customer_rank': 1
        }</field>
    </record>

    <!-- ACTION: Guarantors -->
    <record id="action_finance_guarantors" model="ir.actions.act_window">
        <field name="name">Guarantors</field>
        <field name="res_model">res.partner</field>
        <field name="view_mode">list,form</field>
        <field name="domain">[('finance_partner_type', '=', 'guarantor')]</field>
        <field name="context">{'default_finance_partner_type': 'guarantor'}</field>
    </record>

    <!-- ACTION: Brokers -->
    <record id="action_finance_brokers" model="ir.actions.act_window">
        <field name="name">Sales Agents / Brokers</field>
        <field name="res_model">res.partner</field>
        <field name="view_mode">list,form</field>
        <field name="domain">[('finance_partner_type', '=', 'broker')]</field>
        <field name="context">{'default_finance_partner_type': 'broker'}</field>
    </record>

    <!-- ACTION: Insurers -->
    <record id="action_finance_insurers" model="ir.actions.act_window">
        <field name="name">Insurance Companies</field>
        <field name="res_model">res.partner</field>
        <field name="view_mode">list,form</field>
        <field name="domain">[('finance_partner_type', '=', 'insurer')]</field>
        <field name="context">{
            'default_finance_partner_type': 'insurer',
            'default_is_company': True
        }</field>
    </record>

    <!-- ACTION: Finance Companies -->
    <record id="action_finance_companies" model="ir.actions.act_window">
        <field name="name">Finance Companies</field>
        <field name="res_model">res.partner</field>
        <field name="view_mode">list,form</field>
        <field name="domain">[('finance_partner_type', '=', 'finance_company')]</field>
        <field name="context">{
            'default_finance_partner_type': 'finance_company',
            'default_is_company': True
        }</field>
    </record>

    <!-- ACTION: Suppliers -->
    <record id="action_finance_suppliers" model="ir.actions.act_window">
        <field name="name">Suppliers / Dealers</field>
        <field name="res_model">res.partner</field>
        <field name="view_mode">list,form</field>
        <field name="domain">[('finance_partner_type', '=', 'supplier')]</field>
        <field name="context">{
            'default_finance_partner_type': 'supplier',
            'default_is_company': True
        }</field>
    </record>

    <!-- MENUS -->
    <menuitem id="menu_finance_partners_root"
              name="Partners"
              parent="asset_finance.menu_finance_root"
              sequence="20"/>

    <menuitem id="menu_finance_customers"
              name="Customers (Hirers)"
              parent="menu_finance_partners_root"
              action="action_finance_customers"
              sequence="10"/>

    <menuitem id="menu_finance_guarantors"
              name="Guarantors"
              parent="menu_finance_partners_root"
              action="action_finance_guarantors"
              sequence="20"/>

    <menuitem id="menu_finance_brokers"
              name="Sales Agents / Brokers"
              parent="menu_finance_partners_root"
              action="action_finance_brokers"
              sequence="30"/>

    <menuitem id="menu_finance_insurers"
              name="Insurance Companies"
              parent="menu_finance_partners_root"
              action="action_finance_insurers"
              sequence="40"/>

    <menuitem id="menu_finance_companies"
              name="Finance Companies"
              parent="menu_finance_partners_root"
              action="action_finance_companies"
              sequence="50"/>

    <menuitem id="menu_finance_suppliers"
              name="Suppliers / Dealers"
              parent="menu_finance_partners_root"
              action="action_finance_suppliers"
              sequence="60"/>
</odoo>
```

### Step 5: Data Migration Script

You need to migrate existing boolean flags to the new selection field:

```python
# scripts/migrate_partner_types.py

# Map old boolean fields to new selection values
def migrate_partner_types(env):
    Partner = env['res.partner']

    # Map boolean fields to new type (in priority order)
    migrations = [
        ('is_finance_joint_hirer', 'co_borrower'),
        ('is_finance_broker', 'broker'),
        ('is_finance_guarantor', 'guarantor'),
        # Note: is_finance_customer doesn't exist yet,
        # we'll infer it from contracts below
    ]

    for boolean_field, type_value in migrations:
        if boolean_field in Partner._fields:
            partners = Partner.search([(boolean_field, '=', True)])
            print(f"Migrating {len(partners)} partners with {boolean_field} → {type_value}")
            partners.write({'finance_partner_type': type_value})

    # Set customers based on contracts
    Contract = env['finance.contract']
    hirers = Contract.search([]).mapped('hirer_id')
    hirers_without_type = hirers.filtered(lambda p: not p.finance_partner_type)
    print(f"Setting {len(hirers_without_type)} hirers as 'customer'")
    hirers_without_type.write({'finance_partner_type': 'customer'})

    # Set suppliers based on supplier_rank
    suppliers = Partner.search([
        ('supplier_rank', '>', 0),
        ('finance_partner_type', '=', False)
    ])
    print(f"Setting {len(suppliers)} suppliers as 'supplier'")
    suppliers.write({'finance_partner_type': 'supplier'})

    env.cr.commit()
    print("✅ Migration complete!")

# Run with: docker-compose exec web odoo shell -d your_db
# Then: exec(open('scripts/migrate_partner_types.py').read())
# Then: migrate_partner_types(env)
```

---

## 📊 Final Comparison Table

| Feature | Boolean Fields | Selection Field | Hybrid |
|---------|---------------|-----------------|--------|
| **Simplicity** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Clean Code** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **UI Clarity** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Data Integrity** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Reporting** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Storage** | ⭐⭐ (6 columns) | ⭐⭐⭐⭐⭐ (1 column) | ⭐⭐⭐⭐ |
| **Migration** | ⭐⭐⭐⭐ (3 exist) | ⭐⭐ (need script) | ⭐⭐ |

---

## ✅ RECOMMENDATION

### **Use Single Selection Field** ⭐

**Why:**
1. ✅ Cleaner, simpler code
2. ✅ Better user experience (one dropdown vs 6 checkboxes)
3. ✅ Standard Odoo pattern
4. ✅ Better performance
5. ✅ Easier reporting
6. ✅ Most finance partners have ONE primary role

**When to use Hybrid:**
- If partners commonly have multiple roles
- If you need complex role combinations

**When to use Boolean:**
- If roles are completely independent
- If you need maximum flexibility at the cost of complexity

---

## 🚀 Next Steps

1. ✅ Review the migration script
2. ✅ Backup your database
3. ✅ Update res_partner.py with single selection field
4. ✅ Update all domain filters in contract.py
5. ✅ Update partner form view
6. ✅ Create partner menus XML
7. ✅ Run migration script
8. ✅ Test thoroughly
9. ✅ Upgrade module

Total implementation time: ~30-45 minutes
