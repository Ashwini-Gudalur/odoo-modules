from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
class ProductTemplate(models.Model):
    _inherit = "product.template"
    

    x_product_scheduleh = fields.Boolean('Is Schedule h', default=False)

    @api.model
    def create(self,values):
        ret =super(ProductTemplate, self).create(values)
  
        # sales_price = values.get('list_price') or 0
        # mrp = values.get('mrp')
        sales_price = values.get('list_price') or self.list_price
        mrp =  values.get('mrp') or self.env['product.product'].search([('product_tmpl_id','=',self.id)]).mrp
        default_tax_percent = self.env['ir.values'].get_default('sale.config.settings', 'default_tax_percent') or 0
        if sales_price != 'None' and mrp != 'None':
            if default_tax_percent>0:
                sp_incl_tax = float(sales_price) + (float(sales_price) * (float(default_tax_percent)/100))
            else:
                sp_incl_tax = float(sales_price)
            if(sp_incl_tax > mrp):
                print("..................ret.type",ret.type)
                if ret.type != 'service':
                    raise UserError(
                        _('sale price %f and include sale+ tax is %f is more than mrp %f') %
                        (float(sales_price),float(sp_incl_tax),float(mrp)))
        return ret

    def write(self,values):
        sales_price = values.get('list_price') or self.list_price
        mrp =  values.get('mrp') or self.env['product.product'].search([('product_tmpl_id','=',self.id)]).mrp
        if sales_price and mrp:
            default_tax_percent = self.env['ir.values'].get_default('sale.config.settings', 'default_tax_percent') or 0
            if sales_price != 'None' and mrp != 'None':
                if default_tax_percent>0:
                    sp_incl_tax = float(sales_price) + (float(sales_price) * (float(default_tax_percent)/100))
                else:
                    sp_incl_tax = float(sales_price)
                if(sp_incl_tax > mrp):
                    if self.type != 'service':
                        raise UserError(
                            _('sale price %f and include sale+ tax is %f is more than mrp %f') %
                            (float(sales_price),float(sp_incl_tax),float(mrp)))
        return super(ProductTemplate, self).write(values)


class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def create(self,values):
        print("...........................................5555555555")
        ret = super(stock_production_lot, self).create(values)
        if not self._context.get('show_reserved' ,False):
            sale_price = values.get('sale_price') or self.sale_price
            mrp = values.get('mrp') or self.mrp
            _logger.error(".....................sale_price = %s",sale_price)
            _logger.error(".....................mrp = %s",mrp)
            default_tax_percent = self.env['ir.values'].get_default('sale.config.settings', 'default_tax_percent') or 0
            if sale_price != 'None' and mrp != 'None':
                if default_tax_percent>0:
                    sp_incl_tax = float(sale_price) + (float(sale_price) * (float(default_tax_percent)/100))
                else:
                    sp_incl_tax = float(sale_price)
                _logger.error(".....................sp_incl_tax = %s",sp_incl_tax)
                print(".................",sp_incl_tax)
                print(".................",mrp)
                if(sp_incl_tax > mrp):
                    print("...........................3")
                    raise UserError(
                        _('sale price %f and include sale+ tax is %f is more than mrp %f') %
                        (float(sale_price),float(sp_incl_tax),float(mrp)))
            # print("...................................",values)
        return ret

    def write(self,values):
        print("..................",values)
        res = super(stock_production_lot, self).write(values)
        if not self._context.get('show_reserved' ,False):
            sale_price = values.get('sale_price') or self.sale_price
            print("....................... self.mrp....", self.mrp)
            mrp =  values.get('mrp') or self.mrp
            print("............................",mrp)
            _logger.error(".....................sale_price = %s",sale_price)
            _logger.error(".....................mrp = %s",mrp)
            default_tax_percent = self.env['ir.values'].get_default('sale.config.settings', 'default_tax_percent') or 0
            if sale_price != 'None' and mrp != 'None':
                if default_tax_percent>0:
                    sp_incl_tax = float(sale_price) + (float(sale_price) * (float(default_tax_percent)/100))
                else:
                    sp_incl_tax = float(sale_price)
                _logger.error(".....................sp_incl_tax = %s",sp_incl_tax)
                print("......................",sp_incl_tax)
                print("......................",mrp)
                if(sp_incl_tax > mrp):
                    
                    raise UserError(
                        _('sale price %f and include sale+ tax is %f is more than mrp %f') %
                    (float(sale_price),float(sp_incl_tax),float(mrp)))
        return res