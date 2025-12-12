Docker Commands:

Start:   
  
  docker-compose up

Restart web only:  
  
  docker-compose restart web

Use command line to upgrade asset finance module:  

  docker-compose run --rm web -d vfs -u asset_finance --stop-after-init --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/opt/odoo/addons

Use command line to access odoo shell to run Python script:

   docker-compose run --rm web shell -d vfs --stop-after-init --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/opt/odoo/addons

Use command line to execute Python script in PowerShell:

  Get-Content xxxxxx.py | docker-compose exec -T web python3 /opt/odoo/odoo-bin shell -c /etc/odoo/odoo.conf -d vfs

Uninstall Asset Finance Theme Module (in the case the theme break odoo UI and not able to access from Apps UI)

First Step is to execute command line:

    docker-compose run --rm web shell -d vfs --stop-after-init --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/opt/odoo/addons

Second Step is to past the below Python script:

# 1. Find the module
module = env['ir.module.module'].search([('name', '=', 'asset_finance_theme')])

# 2. Uninstall it immediately
if module:
    module.button_immediate_uninstall()
    env.cr.commit()
    print("SUCCESS: Module uninstalled.")
else:
    print("WARNING: Module not found (maybe already uninstalled?)")

Third step is to execute exit() to exit shell