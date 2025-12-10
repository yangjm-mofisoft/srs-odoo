-- =====================================================
-- Asset Finance Module - Test Data Setup Script
-- =====================================================
-- This SQL script creates sample test data for the Asset Finance module
-- Run this script after module installation to quickly set up test environment
--
-- IMPORTANT: This is for TESTING ONLY - DO NOT run in production!
-- =====================================================

-- Set variables (adjust company_id as needed)
\set company_id 1
\set currency_id 3  -- Assuming SGD (adjust based on your setup)

-- =====================================================
-- 1. CREATE TEST PARTNERS (CUSTOMERS)
-- =====================================================

-- Test Customer 1: John Doe
INSERT INTO res_partner (
    name, email, phone, street, city, zip, country_id,
    company_id, vat, is_company, customer_rank,
    create_date, write_date
) VALUES (
    'John Doe Test',
    'john.doe@test.com',
    '+65 1234 5678',
    '123 Test Street',
    'Singapore',
    '123456',
    (SELECT id FROM res_country WHERE code = 'SG'),
    :company_id,
    'S1234567A',
    false,
    1,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Test Customer 2: Jane Smith
INSERT INTO res_partner (
    name, email, phone, street, city, zip, country_id,
    company_id, vat, is_company, customer_rank,
    create_date, write_date
) VALUES (
    'Jane Smith Test',
    'jane.smith@test.com',
    '+65 8765 4321',
    '456 Sample Avenue',
    'Singapore',
    '654321',
    (SELECT id FROM res_country WHERE code = 'SG'),
    :company_id,
    'S7654321B',
    false,
    1,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Test Customer 3: ABC Company
INSERT INTO res_partner (
    name, email, phone, street, city, country_id,
    company_id, vat, is_company, customer_rank,
    create_date, write_date
) VALUES (
    'ABC Company Test Pte Ltd',
    'info@abctest.com',
    '+65 6123 4567',
    '789 Business Park',
    'Singapore',
    (SELECT id FROM res_country WHERE code = 'SG'),
    :company_id,
    '201234567K',
    true,
    1,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Test Guarantor
INSERT INTO res_partner (
    name, email, phone, vat, company_id, customer_rank,
    create_date, write_date
) VALUES (
    'Robert Brown (Guarantor)',
    'robert.brown@test.com',
    '+65 9876 5432',
    'S9876543C',
    :company_id,
    0,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Test Supplier/Dealer
INSERT INTO res_partner (
    name, email, phone, is_company, supplier_rank,
    company_id, ref,
    create_date, write_date
) VALUES (
    'Premium Auto Dealer Test',
    'sales@premiumauto.test',
    '+65 6234 5678',
    true,
    1,
    :company_id,
    'DEALER001',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 2. CREATE TEST VEHICLES (FLEET)
-- =====================================================

-- Create Fleet Vehicle Brand
INSERT INTO fleet_vehicle_model_brand (name, create_date, write_date)
VALUES ('Toyota Test', NOW(), NOW())
ON CONFLICT DO NOTHING;

INSERT INTO fleet_vehicle_model_brand (name, create_date, write_date)
VALUES ('Honda Test', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Create Fleet Vehicle Models
INSERT INTO fleet_vehicle_model (
    brand_id, name, create_date, write_date
) VALUES (
    (SELECT id FROM fleet_vehicle_model_brand WHERE name = 'Toyota Test' LIMIT 1),
    'Corolla Altis Test',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

INSERT INTO fleet_vehicle_model (
    brand_id, name, create_date, write_date
) VALUES (
    (SELECT id FROM fleet_vehicle_model_brand WHERE name = 'Honda Test' LIMIT 1),
    'Civic Test',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Create Test Vehicles
INSERT INTO fleet_vehicle (
    name, license_plate, model_id, model_year,
    company_id, create_date, write_date
) VALUES (
    'SXX1234A - Toyota Corolla',
    'SXX1234A',
    (SELECT id FROM fleet_vehicle_model WHERE name = 'Corolla Altis Test' LIMIT 1),
    2023,
    :company_id,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

INSERT INTO fleet_vehicle (
    name, license_plate, model_id, model_year,
    company_id, create_date, write_date
) VALUES (
    'SXX5678B - Honda Civic',
    'SXX5678B',
    (SELECT id FROM fleet_vehicle_model WHERE name = 'Civic Test' LIMIT 1),
    2023,
    :company_id,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

INSERT INTO fleet_vehicle (
    name, license_plate, model_id, model_year,
    company_id, create_date, write_date
) VALUES (
    'SXX9999C - Toyota Corolla',
    'SXX9999C',
    (SELECT id FROM fleet_vehicle_model WHERE name = 'Corolla Altis Test' LIMIT 1),
    2022,
    :company_id,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 3. CREATE FINANCE ASSETS (from vehicles)
-- =====================================================

-- Asset Type 1
INSERT INTO finance_asset (
    vehicle_id, asset_type, purchase_price, status,
    create_date, write_date
)
SELECT
    id,
    'motor_vehicle',
    50000.00,
    'available',
    NOW(),
    NOW()
FROM fleet_vehicle
WHERE license_plate = 'SXX1234A'
AND NOT EXISTS (
    SELECT 1 FROM finance_asset WHERE vehicle_id = fleet_vehicle.id
);

-- Asset Type 2
INSERT INTO finance_asset (
    vehicle_id, asset_type, purchase_price, status,
    create_date, write_date
)
SELECT
    id,
    'motor_vehicle',
    45000.00,
    'available',
    NOW(),
    NOW()
FROM fleet_vehicle
WHERE license_plate = 'SXX5678B'
AND NOT EXISTS (
    SELECT 1 FROM finance_asset WHERE vehicle_id = fleet_vehicle.id
);

-- Asset Type 3
INSERT INTO finance_asset (
    vehicle_id, asset_type, purchase_price, status,
    create_date, write_date
)
SELECT
    id,
    'motor_vehicle',
    40000.00,
    'available',
    NOW(),
    NOW()
FROM fleet_vehicle
WHERE license_plate = 'SXX9999C'
AND NOT EXISTS (
    SELECT 1 FROM finance_asset WHERE vehicle_id = fleet_vehicle.id
);

-- =====================================================
-- 4. CREATE FINANCE TERMS
-- =====================================================

INSERT INTO finance_term (name, months, create_date, write_date)
VALUES ('12 Months', 12, NOW(), NOW())
ON CONFLICT DO NOTHING;

INSERT INTO finance_term (name, months, create_date, write_date)
VALUES ('24 Months', 24, NOW(), NOW())
ON CONFLICT DO NOTHING;

INSERT INTO finance_term (name, months, create_date, write_date)
VALUES ('36 Months', 36, NOW(), NOW())
ON CONFLICT DO NOTHING;

INSERT INTO finance_term (name, months, create_date, write_date)
VALUES ('48 Months', 48, NOW(), NOW())
ON CONFLICT DO NOTHING;

INSERT INTO finance_term (name, months, create_date, write_date)
VALUES ('60 Months', 60, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- =====================================================
-- 5. CREATE FINANCIAL PRODUCTS
-- =====================================================

-- Hire Purchase 5-Year
INSERT INTO finance_product (
    name, product_type, default_int_rate,
    min_months, max_months, step_months,
    active, create_date, write_date
) VALUES (
    'Hire Purchase 5-Year Test',
    'hp',
    8.5,
    12,
    60,
    12,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Hire Purchase 7-Year
INSERT INTO finance_product (
    name, product_type, default_int_rate,
    min_months, max_months, step_months,
    active, create_date, write_date
) VALUES (
    'Hire Purchase 7-Year Test',
    'hp',
    7.5,
    12,
    84,
    12,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Leasing 3-Year
INSERT INTO finance_product (
    name, product_type, default_int_rate,
    default_rv_percentage, annual_mileage_limit,
    min_months, max_months, step_months,
    active, create_date, write_date
) VALUES (
    'Leasing 3-Year Test',
    'leasing',
    6.5,
    30.0,
    15000,
    12,
    36,
    12,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 6. CREATE PENALTY RULES
-- =====================================================

INSERT INTO finance_penalty_rule (
    name, method, rate, grace_period_days,
    active, create_date, write_date
) VALUES (
    'Daily Penalty 0.05% Test',
    'daily_percent',
    0.05,
    7,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

INSERT INTO finance_penalty_rule (
    name, method, fixed_amount, grace_period_days,
    active, create_date, write_date
) VALUES (
    'Fixed $50 Late Fee Test',
    'fixed_one_time',
    50.00,
    7,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 7. CREATE MASTER DATA (CHARGES)
-- =====================================================

INSERT INTO finance_charge (
    name, type, amount, active,
    create_date, write_date
) VALUES (
    'Admin Fee - Standard Test',
    'admin',
    150.00,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

INSERT INTO finance_charge (
    name, type, amount, active,
    create_date, write_date
) VALUES (
    'Processing Fee Test',
    'other',
    100.00,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 8. UPDATE PARTNER FLAGS
-- =====================================================

-- Mark customers as finance customers
UPDATE res_partner
SET is_finance_customer = true
WHERE name IN ('John Doe Test', 'Jane Smith Test', 'ABC Company Test Pte Ltd');

-- Mark guarantor
UPDATE res_partner
SET is_finance_guarantor = true
WHERE name = 'Robert Brown (Guarantor)';

-- =====================================================
-- 9. CREATE SAMPLE CONTRACTS (Optional - Commented Out)
-- =====================================================
-- Uncomment below to create sample draft contracts
-- WARNING: Requires proper account_id configuration

/*
-- Sample Contract 1: Draft Status
INSERT INTO finance_contract (
    agreement_no,
    product_id,
    asset_id,
    hirer_id,
    agreement_date,
    cash_price,
    down_payment,
    int_rate_pa,
    no_of_inst,
    ac_status,
    currency_id,
    period_type,
    interest_method,
    payment_scheme,
    installment_type,
    -- Note: Requires valid journal and account IDs
    journal_id,
    asset_account_id,
    income_account_id,
    unearned_interest_account_id,
    create_date,
    write_date
) VALUES (
    'TEST-HP-001',
    (SELECT id FROM finance_product WHERE name = 'Hire Purchase 5-Year Test' LIMIT 1),
    (SELECT id FROM finance_asset LIMIT 1),
    (SELECT id FROM res_partner WHERE name = 'John Doe Test' LIMIT 1),
    CURRENT_DATE,
    50000.00,
    10000.00,
    8.5,
    (SELECT id FROM finance_term WHERE months = 60 LIMIT 1),
    'draft',
    :currency_id,
    'monthly',
    'rule78',
    'arrears',
    'annuity',
    1,  -- Replace with actual journal_id
    1,  -- Replace with actual asset_account_id
    1,  -- Replace with actual income_account_id
    1,  -- Replace with actual unearned_interest_account_id
    NOW(),
    NOW()
);
*/

-- =====================================================
-- 10. VERIFICATION QUERIES
-- =====================================================

-- Check created data
SELECT '=== TEST DATA VERIFICATION ===' as status;

SELECT 'Partners Created:' as item, COUNT(*) as count
FROM res_partner
WHERE name LIKE '%Test%' OR email LIKE '%test.com';

SELECT 'Vehicles Created:' as item, COUNT(*) as count
FROM fleet_vehicle
WHERE license_plate LIKE 'SXX%';

SELECT 'Finance Assets Created:' as item, COUNT(*) as count
FROM finance_asset
WHERE vehicle_id IN (SELECT id FROM fleet_vehicle WHERE license_plate LIKE 'SXX%');

SELECT 'Financial Products Created:' as item, COUNT(*) as count
FROM finance_product
WHERE name LIKE '%Test%';

SELECT 'Finance Terms Available:' as item, COUNT(*) as count
FROM finance_term;

SELECT 'Penalty Rules Created:' as item, COUNT(*) as count
FROM finance_penalty_rule
WHERE name LIKE '%Test%';

SELECT 'Charges Created:' as item, COUNT(*) as count
FROM finance_charge
WHERE name LIKE '%Test%';

-- =====================================================
-- 11. CLEANUP SCRIPT (Run to remove test data)
-- =====================================================
-- Uncomment to remove all test data

/*
-- Delete in reverse order to respect foreign keys
DELETE FROM finance_contract WHERE agreement_no LIKE 'TEST-%';
DELETE FROM finance_asset WHERE vehicle_id IN (SELECT id FROM fleet_vehicle WHERE license_plate LIKE 'SXX%');
DELETE FROM fleet_vehicle WHERE license_plate LIKE 'SXX%';
DELETE FROM fleet_vehicle_model WHERE name LIKE '%Test%';
DELETE FROM fleet_vehicle_model_brand WHERE name LIKE '%Test%';
DELETE FROM finance_charge WHERE name LIKE '%Test%';
DELETE FROM finance_penalty_rule WHERE name LIKE '%Test%';
DELETE FROM finance_product WHERE name LIKE '%Test%';
DELETE FROM res_partner WHERE email LIKE '%test.com' OR name LIKE '%Test%';

SELECT 'Test data cleaned up successfully!' as status;
*/

-- =====================================================
-- END OF SCRIPT
-- =====================================================

SELECT '=== TEST DATA SETUP COMPLETE ===' as status;
SELECT 'You can now create test users and start testing!' as next_step;
SELECT 'See TESTING_ACCOUNTS_GUIDE.md for user creation steps' as documentation;

-- =====================================================
-- NOTES:
-- =====================================================
-- 1. Adjust company_id and currency_id variables at the top
-- 2. Ensure Chart of Accounts is configured before creating contracts
-- 3. Sample contracts are commented out - configure accounts first
-- 4. Run cleanup section to remove test data when done
-- 5. This script is idempotent - safe to run multiple times
-- =====================================================
