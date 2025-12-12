@echo off
REM Script to run test data setup in Odoo Docker container
REM Usage: run_test_data.bat <database_name>

SET DATABASE=%1
IF "%DATABASE%"=="" SET DATABASE=vfs

echo ==================================================
echo Running Enhanced Test Data Setup Script
echo Database: %DATABASE%
echo ==================================================

REM Copy script to mounted location
copy testing\scripts\setup_test_data_02_enhanced.py custom_addons\

REM Run using Odoo shell
docker-compose exec -T web odoo shell -d %DATABASE% --no-http < custom_addons\setup_test_data_02_enhanced.py

REM Clean up
del custom_addons\setup_test_data_02_enhanced.py

echo ==================================================
echo Script execution completed!
echo ==================================================
pause
