#!/bin/bash
# Script to run test data setup in Odoo Docker container
# Usage: ./run_test_data.sh <database_name>

DATABASE=${1:-vfs}

echo "=================================================="
echo "Running Enhanced Test Data Setup Script"
echo "Database: $DATABASE"
echo "=================================================="

# Copy script to a mounted location
cp testing/scripts/setup_test_data_02_enhanced.py custom_addons/

# Run using Odoo shell
docker-compose exec -T web ./odoo-bin shell -c /etc/odoo/odoo.conf -d "$DATABASE" --db_host=db --no-http < custom_addons/setup_test_data_02_enhanced.py

# Clean up
rm custom_addons/setup_test_data_02_enhanced.py

echo "=================================================="
echo "Script execution completed!"
echo "=================================================="
