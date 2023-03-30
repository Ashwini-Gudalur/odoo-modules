from odoo import models, fields, api, _

class product_product(models.Model):
    
    _inherit = 'product.product'
   
    product_scheduleh = fields.Boolean('Is Schedule H',default=False)
   