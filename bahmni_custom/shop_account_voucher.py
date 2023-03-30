import time
# from lxml import etree
from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import html_translate
from odoo.tools import float_compare


class account_voucher(models.Model):
    _inherit = "account.voucher"

    def getYesOrNo(self, name):
        if(name):
            return 'Yes' if name.lower()=='True'.lower() else 'No'
        return ''

    def _get_partner_attribute_Tribe_details(self,  name, args):
        res = {}
        for account_voucher in self.browse(self.ids):
            partner_obj = self.pool.get("res.partner")
            _logger.error("Partner Id",account_voucher.partner_id)
            if account_voucher.partner_id:
                partner = partner_obj.browse(account_voucher.partner_id.id)
                partner_attri_cnt=self.env["res.partner.attributes"].search([('partner_id','=',partner.id)])
                if len(partner_attri_cnt) > 0:
                    partner_attribute=self.env["res.partner.attributes"].browse(partner_attri_cnt.ids)
                    account_voucher.id = self.getYesOrNo(partner_attribute.x_Is_Tribal)
                else:
                    account_voucher.id =""
            else:
                account_voucher.id =""
        return res

    
  
    shop_id = fields.Many2one('sale.shop',required='True',string ='Collection Point'),
    partner_is_tribe = fields.Char(compute='_get_partner_attribute_Tribe_details', string ='Is Tribe')

class AccountPayment(models.Model):
    _inherit = "account.payment"  

    shop_id = fields.Many2one('sale.shop',required='True',string ='Collection Point')
    partner_is_tribe=fields.Char(compute='_get_partner_attribute_Tribe_details', string ='Is Tribe')

    def _get_partner_attribute_Tribe_details(self):
        for res in self:
            for inv in res.invoice_ids:
                sale_order = self.env['sale.order'].search([('name', '=', inv.origin)])
                if sale_order:
                    res.partner_is_tribe = sale_order.partner_is_tribe

    @api.onchange('invoice_ids')
    def onchange_partner_id(self):
        if self.invoice_ids:
            bill_amount = 0
            for inv in self.invoice_ids:
                bill_amount += inv.amount_total 
                self.shop_id = inv.shop_id.id
            self.bill_amount = bill_amount


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    # shop_id = fields.Many2one('product.pricelist', compute='_compute_pricelist_id', string='Default Pricelist')
    # shop_id = fields.Many2one('sale.shop',related='shop_id.id',string='Shop')

    shop_id = fields.Many2one('sale.shop', string='Shop')
    shop = fields.Char(string='Shop', related='shop_id.name',readonly="1")
  
    #shop_id =fields.mMny2one('sale_id', 'shop_id', type="many2one", relation="sale.shop", string='Shop', store=True, readonly=True)


# class stock_picking_out(osv.osv):
#     _name = 'stock.picking.out'
#     _inherit = 'stock.picking.out'

#     shop_id = fields.Many2one(related='shop_id',string='Shop')

    # _columns = {
    #     'shop_id': fields.related('sale_id', 'shop_id', type="many2one", relation="sale.shop", string='Shop', store=True, readonly=True)
    # }
