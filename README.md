## Install Asset Finance Module:

1. Pull clodes from git
2. Log into odoo as Administrator
3. Click Settings menu, Scroll to the bottom of the page and Click "Activate the developer mode".
4. Go to the Apps menu. In the top menu bar, click "Update Apps List" (this only appears in Developer Mode).A dialog will pop up; click the "Update" button.
5. Refresh Apps module the Asset Finance Management (asset_finance) should appear. Click Activate button to activate the module

## Install MuK themes:

If the above steps are done, go to Apps screen. In Search box remove 'Apps' filter and input MuK to search. All MuK theme modules should appear. Click Activate button of MuK backend Theme Module


# Docker Commands:

**Start:**   
  
  `docker-compose up`

**Restart web only:**
  
  `docker-compose restart web`

**Use command line to upgrade asset finance module:**

  `docker-compose run --rm web -d vfs -u asset_finance --stop-after-init --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/opt/odoo/addons`

**Use command line to access odoo shell to run Python script:**

   `docker-compose run --rm web shell -d vfs --stop-after-init --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/opt/odoo/addons`

**Use command line to execute Python script in PowerShell:**

  `Get-Content xxxxxx.py | docker-compose exec -T web python3 /opt/odoo/odoo-bin shell -c /etc/odoo/odoo.conf -d vfs`

**Uninstall Asset Finance Theme Module (in the case the theme break odoo UI and not able to access from Apps UI)**

**First Step is to execute command line:**

    `docker-compose run --rm web shell -d vfs --stop-after-init --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/opt/odoo/addons`

**Second Step is to past the below Python script:**

1. Find the module
   
    `module = env['ir.module.module'].search([('name', '=', 'asset_finance_theme')])`

3. Uninstall it immediately
   
```
if module:
    module.button_immediate_uninstall()
    env.cr.commit()
    print("SUCCESS: Module uninstalled.")
else:
    print("WARNING: Module not found (maybe already uninstalled?)")
```

Third step is to execute exit() to exit shell

**In case the module is uninstalled and folder is deleted but the module still appears in Apps screen, do below steps to remove from odoo db**

1. execute command line:

  `docker exec -it <db container name>  psql -U odoo -d vfs -c "DELETE FROM ir_module_module WHERE name = '<module name>';"`

  db container name:  srs-odoo_db_1 in test server
  module name: the module to be deleted. for example asset_finance

2. Restart odoo web container. In test server it is `docker-compose -f docker-compose.server.yml restart web`

3. Deep delete the module using below command line:

  `docker exec -it <db container name> psql -U odoo -d vfs -c "DELETE FROM ir_model_data WHERE module = '<module name>';"`

4. Confirm no more table related to the module in odoo db"

  `docker exec -it <db container name> psql -U odoo -d vfs -c "\dt <module prefix i.e. asset>*;"`
