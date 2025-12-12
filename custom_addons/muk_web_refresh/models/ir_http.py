from odoo import models


class IrHttp(models.AbstractModel):

    _inherit = 'ir.http'

    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def session_info(self):
        result = super().session_info()
        try:
            # Try to get the parameter value
            param_value = self.env['ir.config_parameter'].sudo().get_param(
                'muk_web_refresh.pager_autoload_interval',
                default='30000'
            )
            result['pager_autoload_interval'] = int(param_value or 30000)
        except (AttributeError, TypeError):
            # Fallback to default if method not available (Odoo 19 compatibility)
            result['pager_autoload_interval'] = 30000
        return result
