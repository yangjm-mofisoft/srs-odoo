New Menu Structure:
Asset Finance
├── Dashboard (sequence: 0)
│
├── Operations (sequence: 10)
│   ├── Contracts
│   ├── Receipts
│   └── Payments
│
├── Partners (sequence: 20) ⭐ NEW - Dedicated partner management
│   ├── Customers (individuals & companies without business type)
│   ├── Sales Agents / Brokers
│   ├── Insurance Companies
│   ├── Finance Companies
│   └── Suppliers / Dealers
│
├── Master Data (sequence: 30) ✅ REORGANIZED
│   ├── Assets
│   └── Financial Products (moved from Configuration)
│
├── Accounting (sequence: 40)
│   ├── Journal Entries
│   └── Journal Items
│
└── Configuration (sequence: 99) ✅ CLEANED UP
    ├── Chart of Accounts
    ├── Taxes
    ├── Penalty Rules
    └── Users

Logical Grouping:

Operations = Day-to-day activities (Contracts, Receipts, Payments)
Partners = All partner types properly categorized
Master Data = Reference data (Assets, Financial Products)
Accounting = Accounting-specific functions
Configuration = System settings