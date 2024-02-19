from math import fabs
from pickle import FALSE
from odoo import fields, models,api
from odoo.exceptions import UserError, ValidationError

import logging

from datetime import datetime, timedelta
from odoo.fields import Date

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import logging
_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError, ValidationError

class sale_order(models.Model):
    
    _inherit = "sale.order"
    shop_location_id = fields.Many2one('stock.location', 'Shop Location')


    @api.model
    def create(self, vals):
        ret =super(sale_order, self).create(vals)
        ret.shop_location_id = ret.shop_id.location_id.id
        return ret

    def _get_product_context(self,  shop_id,prodlot_id):
        shop_obj = self.env['sale.shop']
        shop = shop_obj.browse( shop_id)
        prod_context = {}
        if(not shop):
            return {}
        if shop:
            location_id = shop.warehouse_id and shop.warehouse_id.lot_stock_id.id
            if location_id:
                prod_context['location'] = location_id
                prod_context['prodlot_id'] = prodlot_id
                prod_context['compute_child'] = False
        return prod_context

    def _get_prodlot_context(self,  shop_id):
        shop_obj = self.env['sale.shop']
        shop = shop_obj.browse(shop_id)
        prodlot_context = {}
        if(not shop):
            return {}
        if shop:
            location_id = shop.warehouse_id and shop.warehouse_id.lot_stock_id.id
            if location_id:
                prodlot_context['location_id'] = location_id
                prodlot_context['search_in_child'] = False
        return prodlot_context

    def is_qty_avail_against_batches(self,shop_id):
        res = []
        sale_order_line=self.env["sale.order.line"].search([('order_id','=',self.ids[0])])
        if len(sale_order_line) > 0:
            for sol in sale_order_line:
                soltemp= self.env["sale.order.line"].browse(sol.ids)
                template = self.get_prod_template(sol)
                stock_prod_lot = self.env['stock.production.lot']
                prod_prod = self.env['product.product']
                prodlot_context = self._get_prodlot_context(shop_id)
                if soltemp.location_lot_line_id:
                    if(template.type != 'service'):
                        if not  soltemp.lot_id :
                            soltemp.lot_id = soltemp.location_lot_line_id.lot_id.id
                            soltemp.onchange_location_lot_line_id()
                            soltemp.onchange_lot_id()
                if(template.type != 'service'):
                    if soltemp.lot_id.id >0 and soltemp.lot_id.id>0:
                        prod_context = self._get_product_context(shop_id,soltemp.lot_id.id)
                        prodlot = stock_prod_lot.browse( soltemp.lot_id.id)
                        product_id = []
                        product_id.append(prodlot.product_id.id)
                        # actual_stock = prod_prod._get_actual_stock( product_id, '', [], prod_context)
                        # actual_qty = actual_stock[prodlot.product_id.id]
                        if soltemp.lot_id.sale_price < soltemp.price_unit:
                            res.append({'error':'Unit price is bigger then Lots/Serial Sell price ','item':soltemp.name})
                        if(soltemp.product_uom_qty>prodlot.product_id.actual_stock):
                            res.append({'error':'Not enough inventory','item':soltemp.name, 'Available':prodlot.product_id.actual_stock, 'Requested':soltemp.product_uom_qty})
                        if (soltemp.lot_id.life_date):
                            if soltemp.lot_id.life_date <= Date.today():
                                res.append({'error':'Product Expire..'})
                        sales_price = prodlot.sale_price
                        mrp = prodlot.mrp
                        tax_amount=0.0
                        if sales_price and mrp:
                            for tax in soltemp.tax_id:
                                tax_amount = tax_amount + tax.amount
                            _logger.error("Taxes = %f",tax_amount)
                        sp_incl_tax = sales_price + sales_price*tax_amount
                        print(".............................",sp_incl_tax)
                        print(".............................mrp",mrp)
                        if(sp_incl_tax>mrp):
                            res.append({'error':'Sales Price Including Tax more than MRP','item':soltemp.name, 'Sales With Tax':sp_incl_tax, 'MRP':mrp})
                    else:
                        #lot_id missing
                        if soltemp.product_id.tracking == 'lot':
                            res.append({'error':'No batch number provided','item':soltemp.name})
        return res


    def action_confirm(self):
        # assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        # wf_service = netsvc.LocalService('workflow')
        # wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)
        sale_order_temp=self.env["sale.order"].browse(self.ids)
        if(sale_order_temp.care_setting == 'opd'):
            multicat = self.is_a_multi_cat_so()
            if multicat == True :
                raise UserError(
                
                    'You cannot have items from different departments in same quotation.')
        errors = self.is_qty_avail_against_batches(sale_order_temp.shop_id.id)
        for line in self.order_line:
            if line.lot_id:
                stock_records = self.env['stock.quant'].read_group([('lot_id','=',line.lot_id.id),('location_id','=',self.shop_id.location_id.id),('product_id','=',line.product_id.id),('location_id.usage','=', 'internal')], fields=['location_id', 'qty'],
                                                        groupby=['location_id','lot_id'])
                if stock_records:
                    print('LOTTTTT+++++++++++++')
                    for record in stock_records:
                        if record['qty'] < line.product_uom_qty:
                            raise UserError('Quantity is more then lot/serial available Quantity')

        if(len(errors)>0):
            raise ValidationError(
            
                ('Cannot procced with sale because of the following errors. %s')
                %(errors))

        return super(sale_order, self).action_confirm()

    def is_a_multi_cat_so(self):
        sale_order_line=self.env["sale.order.line"].search([('order_id','=',self.ids)])
        if len(sale_order_line) == 1:
            return False
        else:
            if len(sale_order_line) < 1:
                return False
            else:
                commoncatlist=self.env["product.category"].search([('name','=','Common')])
                commoncat = commoncatlist.id
                not_a_common_sol = self.get_not_a_common_sale_order_line(sale_order_line,commoncat)
                if not not_a_common_sol:
                    return False
                else:
                    catIds = self.get_array_of_category_ids(not_a_common_sol)
                    catIds.append(commoncat)
                for sol in sale_order_line:
                        _logger.error("Sol=%s",sol)
                        template = self.get_prod_template(sol)
                        if template.categ_id.id not in catIds:
                            return True
            return False


    def get_prod_template(self, sol):

        soltemp= self.env["sale.order.line"].browse(sol.ids)
        product = self.env["product.product"].browse(soltemp.product_id.ids)
        template = self.env["product.template"].browse(product.product_tmpl_id.ids)
        return template

    def get_not_a_common_sale_order_line(self, sale_order_lines,common_cat):
        # get the common's id
        for sol in sale_order_lines:
            template = self.get_prod_template(sol)
            if template.categ_id.id!=common_cat:
                return sol



    def get_array_of_category_ids(self, sol):
        res=[]
        template = self.get_prod_template(sol)
        self.env.cr.execute("""select category_id from syncjob_department_category_mapping where department_name=
                      (select department_name from syncjob_department_category_mapping where category_id="""+str(template.categ_id.id)+")")
        rows = self.env.cr.fetchall()
        for row in rows:
            res.append(row[0])
        return res


    def _get_provs(self):
        self.env.cr.execute('SELECT name FROM providers')
        rows = self.env.cr.fetchall()
        dataset=[]
        for row in rows:
            dataset.append((row[0],row[0]))
        return dataset

    
    care_setting = fields.Selection([('opd', 'OPD'),('ipd', 'IPD')], 'Care Setting',required='True')
    provider_name = fields.Selection(_get_provs, 'Provider')
    
   
    def _prepare_invoice(self):
        ret = super(sale_order, self)._prepare_invoice()
        ret.update({'shop_id':self.shop_id.id,})
        return ret
    
    @api.onchange('shop_id')
    def onchange_shop_id(self):
        res = super(sale_order, self).onchange_shop_id()
        if self.shop_id:
            self.shop_location_id = self.shop_id.location_id.id
            for line in self.order_line:
                if (len(self.env['location.stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',line.order_id.shop_location_id.id)], order='life_date asc'))) == 0:
                    line.location_lot_line_id = False
                    line.lot_id = False
                    line.onchange_lot_id()
                else:
                    for record in self.env['location.stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',line.order_id.shop_location_id.id)], order='life_date asc'):
                        if record.lot_id.life_date >= str(fields.datetime.now()):
                            stock_records = self.env['stock.quant'].search([('lot_id','=',record.lot_id.id),('location_id','=',record.location_id.id),('product_id','=',record.lot_id.product_id.id),('location_id.usage','=', 'internal'),('qty','>', 0)])
                            if sum(stock_records.mapped('qty')) >= line.product_uom_qty:
                                line.location_lot_line_id = record.id
                                line.lot_id = line.location_lot_line_id.lot_id
                                line.onchange_lot_id()
                                break 
                            else:
                                line.location_lot_line_id = False
        return res

class providers(models.Model):
    _name = "providers"
    _description = "Providers in ashwini"
  
    name= fields.Char('Provider Name', required=True)
    


class sale_order_line(models.Model):
    
    _inherit = "sale.order.line"

    categ_id = fields.Many2one('product.category','Category')
    location_lot_line_id = fields.Many2one('location.stock.quant', string="Batch No")


    def lot_id_change(self, lot_id, product_id):
        if not product_id:
            return {}
        if not lot_id:
            prod_obj = self.env['product.product'].browse( product_id)
            return {'value': {'price_unit': prod_obj.list_price}}
        context = context or {}
        stock_prod_lot = self.env['stock.production.lot']
        sale_price = 0.0
        life_date=None
        for prodlot in stock_prod_lot.browse( [lot_id]):
            sale_price =  prodlot.sale_price
            life_date = prodlot.life_date and datetime.strptime(prodlot.life_date, DEFAULT_SERVER_DATETIME_FORMAT)
            if life_date:
                life_date = life_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if (type(life_date) == datetime) else None
        return {'value' : {'price_unit': sale_price ,'expiry_date':life_date}}

    def _prepare_order_line_invoice_line(self,  line, account_id=False):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line( line, account_id=account_id)
        if line.lot_id:
            res["batch_name"] = line.lot_id.name
        res["expiry_date"] = line.expiry_date
        return res


    @api.onchange('lot_id')
    def onchange_lot_id(self):
        res = super(sale_order_line, self).onchange_lot_id()
        if self.lot_id:
            self.price_unit = self.lot_id.sale_price
            self.expiry_date = self.lot_id.life_date
        else:
            self.price_unit = False
            self.expiry_date = False

        return res


    @api.onchange('categ_id')
    def onchange_categ_id(self):
        if self.categ_id:
            return {'domain': {'product_id': [('product_tmpl_id.categ_id', '=', self.categ_id.id)]}}
        else:
            return {'domain': {'product_id': []}}


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(sale_order_line, self).product_id_change()
        for record in self.env['location.stock.quant'].search([('product_id','=',self.product_id.id),('location_id','=',self.order_id.shop_location_id.id)], order='life_date asc'):
            if record.lot_id.life_date >= str(fields.datetime.now()):
                stock_records = self.env['stock.quant'].search([('lot_id','=',record.lot_id.id),('location_id','=',record.location_id.id),('product_id','=',record.lot_id.product_id.id),('location_id.usage','=', 'internal'),('qty','>', 0)])
                if sum(stock_records.mapped('qty')) >= self.product_uom_qty:
                    self.location_lot_line_id = record.id
                    self.lot_id = self.location_lot_line_id.lot_id
                    break
        return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(sale_order_line, self).product_uom_change()
        for record in self.env['location.stock.quant'].search([('product_id','=',self.product_id.id),('location_id','=',self.order_id.shop_location_id.id)], order='life_date asc'):
            if record.lot_id.life_date >= str(fields.datetime.now()):
                stock_records = self.env['stock.quant'].search([('lot_id','=',record.lot_id.id),('location_id','=',record.location_id.id),('product_id','=',record.lot_id.product_id.id),('location_id.usage','=', 'internal'),('qty','>', 0)])
                if sum(stock_records.mapped('qty')) >= self.product_uom_qty:
                    self.location_lot_line_id = record.id
                    self.lot_id = self.location_lot_line_id.lot_id
                    break
                else: 
                    self.location_lot_line_id = False
        return res 
    
    # @api.multi
    # def name_get(self):
    #     res = []
    #     for record in self.env['location.stock.quant'].search([('product_id','=',self.product_id.id)], order='life_date asc'):

    #         lot_name = record.lot_id.name
    #         # if record.lot_id.life_date >= str(fields.datetime.now()):
    #         if(record.lot_id.life_date):
    #             expiry_date = datetime.strptime(record.lot_id.life_date, '%Y-%m-%d %H:%M:%S')
    #             expiry = expiry_date.strftime("%b,%Y")

    #             stock_records = self.env['stock.quant'].search([('lot_id','=',record.lot_id.id),('location_id','=',record.location_id.id),('product_id','=',record.lot_id.product_id.id),('location_id.usage','=', 'internal'),('qty','>', 0)])
    #             if sum(stock_records.mapped('qty')) >0:
    #                 name = "%s [%s] [%s] [%s]" % (lot_name,expiry,record.location_id.name,sum(stock_records.mapped('qty')))

    #                 res.append((record.id, name))
    #     return res


    # @api.onchange('product_id','order_id.shop_id')
    # def lot_id_id_change(self):
    #     if self.product_id and self.order_id.shop_id:
    #         records =self.env['stock.production.lot'].search([('product_id','=',self.product_id.id)])
    #         # print("...........................................",self.product_id.id)
    #         # print("............................................",records)
    #         ids_list =[]
    #         for record in records:
             
    #             for line in record.quant_ids:
    #                 # print("..........................",line.location_id.id)
    #                 # print("..........................",self.order_id.shop_id.location_id.id)
    #                 # print("..........................",line.location_id.id == self.order_id.shop_id.location_id.id and line.qty >0)
    #                 if line.location_id.id == self.order_id.shop_id.location_id.id and line.qty >0:
    #                     ids_list.append(record.id)
    #                     # break
    #                 # print("....................lot",ids_list)
    #         if ids_list :
    #             # print(".................1")
    #             return {'domain': {'lot_id': [('id', 'in', (ids_list))]}}
    #         else:
    #             # print(".................2")
    #             return {'domain': {'lot_id': [('id', '=', [])]}}
    #     else:
    #         # print(".................3")
    #         return {'domain': {'lot_id': [('id', '=', [])]}}

    # @api.onchange('product_id','order_id.shop_id')
    # def location_lot_line_id_id_change(self):
    #     lot_line_list=[]
    #     if self.product_id and self.order_id.shop_id:
    #         records =self.env['location.stock.quant'].search([('location_id','=',self.order_id.shop_id.location_id.id)])
    #         for record in records:
    #             if record.lot_id.product_id == self.product_id and record.lot_id.life_date >= str(fields.datetime.now()):
    #                 lot_line_list.append(record.id)
    #         print("-------------------------------------",lot_line_list)
    #         return {'domain': {'location_lot_line_id': [('id', 'in', (lot_line_list))]}}       
    #     else:
    #         return {'domain': {'location_lot_line_id': [('id', '=', [])]}}

    @api.onchange('location_lot_line_id')
    def onchange_location_lot_line_id(self):
        if self.location_lot_line_id:
            self.lot_id = self.location_lot_line_id.lot_id
        else:
            self.lot_id = False

            
    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            if self.lot_id:
                return self.lot_id.sale_price
            else :
                return product.with_context(pricelist=self.order_id.pricelist_id.id).price
        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom.id)
        final_price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        base_price, currency_id = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(base_price, self.order_id.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)


class stock_production_lot(models.Model):

    _inherit = 'stock.production.lot'
    location_quant_ids = fields.One2many('location.stock.quant', 'lot_id', 'Location Wish',readonly=True)


    @api.model
    def location_create_lot_serial(self):
        records = self.env['stock.production.lot'].search([])
        print("...***************************.",records)
        for record in records:
            locations = record.quant_ids.mapped('location_id')
            # delete
            for line in record.location_quant_ids:
                detele = True
                for location in locations:
                    if line.location_id == location:
                        detele =False
                if detele:
                    line.unlink()
            # create  and update
            for location in locations:
                stock_quant_records = self.env['stock.quant'].search([('lot_id','=',record.id),('location_id','=',location.id)])
                location_stock_quant_records = self.env['location.stock.quant'].search([('lot_id','=',record.id),('location_id','=',location.id)])
                if stock_quant_records:
                    if location_stock_quant_records:
                        location_stock_quant_records.qty = sum(stock_quant_records.mapped('qty'))
                        location_stock_quant_records.product_id =record.product_id.id
                        location_stock_quant_records.life_date =record.life_date
                    else:
                        self.env['location.stock.quant'].create({
                            'location_id': location.id,
                            'qty': sum(stock_quant_records.mapped('qty')),
                            'lot_id' : record.id,'product_id':record.product_id.id,
                             'life_date' : record.life_date
                            })

    def name_get(self):
        res = []
        for record in self.search([('id','in',self.ids)], order='life_date asc'):
            lot_name = record.name
            if not record.life_date:
                res.append((record.id, record.name))
            else:
                name = False
                if(record.life_date):
                    expiry_date = datetime.strptime(record.life_date, '%Y-%m-%d %H:%M:%S')
                    expiry = expiry_date.strftime("%b,%Y")
                    name = "%s [%s]" % (lot_name,expiry)
                else:
                    expiry=False
                    name = "%s [%s]" % (lot_name,expiry)
                if record.life_date >= str(fields.datetime.now()):
                    # lot_name = record.name
                    # if(record.life_date):
                    #     expiry_date = datetime.strptime(record.life_date, '%Y-%m-%d %H:%M:%S')
                    #     expiry = expiry_date.strftime("%b,%Y")
                    # else:
                    #     expiry=False
                        # stock_records = self.env['stock.quant'].read_group([('lot_id','=',record.id),('product_id','=',record.product_id.id),('location_id.usage','=', 'internal'),('qty','>', 0)], fields=['location_id', 'qty'],
                        #                                     groupby=['location_id','lot_id'])
            
                        # for line in stock_records:
                    
                        #     name=""
                        #     name = "%s [%s] [%s] [%s]" % (lot_name,expiry,str(line['location_id']).encode("ascii"),line['qty'])

                        #     res.append((record.id, name))
                    # name = "%s [%s]" % (lot_name,expiry)
                    res.append((record.id, name))
                else :
                    res.append((record.id, name))
        return res


class stock_quant(models.Model):

    _inherit = 'stock.quant'


    @api.model
    def create(self, vals):
        ret =super(stock_quant, self).create(vals)
        print(".................................valsvals",vals)
        locations = ret.lot_id.quant_ids.mapped('location_id')
        # delete
        for line in ret.lot_id.location_quant_ids:
            detele = True
            for location in locations:
                if line.location_id == location:
                    detele =False
            if detele:
                line.unlink()

        #create and update
        for location in locations:
            stock_quant_records = self.env['stock.quant'].search([('lot_id','=',ret.lot_id.id),('location_id','=',location.id)])
            location_stock_quant_records = self.env['location.stock.quant'].search([('lot_id','=',ret.lot_id.id),('location_id','=',location.id)])
            if stock_quant_records:
                if location_stock_quant_records:
                    location_stock_quant_records.qty = sum(stock_quant_records.mapped('qty'))
                    location_stock_quant_records.product_id =ret.lot_id.product_id.id
                    location_stock_quant_records.life_date =ret.lot_id.life_date

                else:
                    self.env['location.stock.quant'].create({
                        'location_id': location.id,
                        'qty': sum(stock_quant_records.mapped('qty')),
                        'lot_id' : ret.lot_id.id,
                        'product_id':ret.lot_id.product_id.id ,
                         'life_date' : ret.lot_id.life_date
                        })

        return ret

    def write(self, vals):
        ret =super(stock_quant, self).write(vals)
        for res in self:
            locations = res.lot_id.quant_ids.mapped('location_id')
            # delete
            for line in res.lot_id.location_quant_ids:
                detele = True
                for location in locations:
                    if line.location_id == location:
                        detele =False
                if detele:
                    line.unlink()

        #create and update
            for location in locations:
                stock_quant_records = self.env['stock.quant'].search([('lot_id','=',res.lot_id.id),('location_id','=',location.id)])
                location_stock_quant_records = self.env['location.stock.quant'].search([('lot_id','=',res.lot_id.id),('location_id','=',location.id)])
                if stock_quant_records:
                    if location_stock_quant_records:
                        location_stock_quant_records.qty = sum(stock_quant_records.mapped('qty'))
                        location_stock_quant_records.product_id =res.lot_id.product_id.id
                        location_stock_quant_records.life_date =res.lot_id.life_date
                    else:
                        self.env['location.stock.quant'].create({
                            'location_id': location.id,
                            'qty': sum(stock_quant_records.mapped('qty')),
                            'lot_id' : res.lot_id.id,
                            'product_id':res.lot_id.product_id.id ,
                            'life_date' : res.lot_id.life_date
                            })

            return ret



class location_stock_quant(models.Model):

    _name = 'location.stock.quant'
    _rec_name="lot_id"

    qty = fields.Float('Quantity')
    location_id = fields.Many2one('stock.location', 'Location')
    product_id = fields.Many2one('product.product', 'Product')
    life_date = fields.Datetime('Expiry Date')
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number')
        
    # def name_get(self):
    #     res = []
    #     for record in self.browse(self.ids):
    #         print("-------------------------------------------",record)
    #         lot_name = record.lot_id.name
    #         # if record.lot_id.life_date >= str(fields.datetime.now()):
    #         if(record.lot_id.life_date):
    #             expiry_date = datetime.strptime(record.lot_id.life_date, '%Y-%m-%d %H:%M:%S')
    #             expiry = expiry_date.strftime("%b,%Y")

    #             stock_records = self.env['stock.quant'].search([('lot_id','=',record.lot_id.id),('location_id','=',record.location_id.id),('product_id','=',record.lot_id.product_id.id),('location_id.usage','=', 'internal'),('qty','>', 0)])
    #             if sum(stock_records.mapped('qty')) >0:
    #                 name = "%s [%s] [%s] [%s]" % (lot_name,expiry,record.location_id.name,sum(stock_records.mapped('qty')))

    #                 res.append((record.id, name))
    #     return res

    @api.multi
    def name_get(self):
        res = []
        qty = []
        for record in self.search([('id','in',self.ids)], order='life_date asc'):
            lot_name = record.lot_id.name
            if(record.lot_id.life_date):
                expiry_date = datetime.strptime(record.lot_id.life_date, '%Y-%m-%d %H:%M:%S')
                expiry = expiry_date.strftime("%b,%Y")

                stock_records = self.env['stock.quant'].search([('lot_id','=',record.lot_id.id),('location_id','=',record.location_id.id),('product_id','=',record.lot_id.product_id.id),('location_id.usage','=', 'internal'),('qty','>', 0)])
                # if sum(stock_records.mapped('qty')) >0:
                #     name = "%s [%s] [%s] [%s]" % (lot_name,expiry,record.location_id.name,sum(stock_records.mapped('qty')))
                if sum(stock_records.mapped('qty')) == 0:
                    continue
                else:
                    qty.append(sum(stock_records.mapped('qty')))
                #     res.append((record.id, name))
                name = "%s [%s] [%s] [%s]" % (lot_name,expiry,record.location_id.name,sum(stock_records.mapped('qty')))
                res.append((record.id, name))
        if not res:
            return super(location_stock_quant, self).name_get()
        else:
            return res

class Product_Picking(models.Model):
    _name = "product.stock.picking"
    
    picking_id = fields.Many2one('stock.picking')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure')
    from_loc = fields.Char( string='From')
    to_loc = fields.Char( string='To')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    qty_done = fields.Float('Qty', default=0.0)
    stock_pack_operation_id = fields.Many2one('stock.pack.operation', 'Operation')
    stock_pack_operation_lot_id = fields.Many2one('stock.pack.operation.lot', 'Operation lot')
    available_qty = fields.Integer(string="Balance")
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')],string="Status")



class Picking(models.Model):
    _inherit = "stock.picking"

    product_pack_lot_ids = fields.One2many('product.stock.picking', 'picking_id', 'Product')
    @api.multi
    def do_new_transfer(self):
        ret = super(Picking, self).do_new_transfer()
        print('DONEEEEEE**********************')
        product_stock_picking_records = self.env['product.stock.picking'].search([('picking_id','=',self.id)])
        for record in product_stock_picking_records:
            record.unlink()
        for line in self.pack_operation_product_ids:
            for lot_line in line.pack_lot_ids:
                self.env['product.stock.picking'].create({
                            'picking_id': self.id,
                            'product_id': line.product_id.id,
                            'product_uom_id' : line.product_uom_id.id,
                            'from_loc':line.from_loc,
                            'to_loc' :line.to_loc,
                            'lot_id' : lot_line.lot_id.id,
                            'qty_done' : lot_line.qty,
                            'stock_pack_operation_id' : line.id,
                            'stock_pack_operation_lot_id' :lot_line.id,
                            'available_qty' : lot_line.available_qty,
                            'state' : self.state
                            })
            # if not line.pack_lot_ids:
            #     self.env['product.stock.picking'].create({
            #                 'picking_id': self.id,
            #                 'product_id': line.product_id.id,
            #                 'product_uom_id' : line.product_uom_id.id,
            #                 'from_loc':line.from_loc,
            #                 'to_loc' :line.to_loc,
            #                 'lot_id' : False,
            #                 'qty_done' : line.qty_done,
            #                 'stock_pack_operation_id' : line.id,
            #                 'stock_pack_operation_lot_id' :False,
            #                 'available_qty' : line.available_qty,
            #                 'state' : self.state
            #                 })
        return ret

    def write(self, vals):
        ret = super(Picking, self).write(vals)
        if self.state == 'done':
            product_stock_picking_records = self.env['product.stock.picking'].search([('picking_id','=',self.id)])
            for record in product_stock_picking_records:
                record.unlink()
            for line in self.pack_operation_product_ids:
                for lot_line in line.pack_lot_ids:
                    self.env['product.stock.picking'].create({
                                'picking_id': self.id,
                                'product_id': line.product_id.id,
                                'product_uom_id' : line.product_uom_id.id,
                                'from_loc':line.from_loc,
                                'to_loc' :line.to_loc,
                                'lot_id' : lot_line.lot_id.id,
                                'qty_done' : lot_line.qty,
                                'stock_pack_operation_id' : line.id,
                                'stock_pack_operation_lot_id' :lot_line.id,
                                'available_qty' : lot_line.available_qty,
                                'state' : self.state
                                })
        
        return ret

class StockPackOperationLot(models.Model):
    _inherit = 'stock.pack.operation.lot'

    @api.onchange('location_lot_line_id')
    def onchange_location_lot_line_id(self):
        if self.location_lot_line_id:
            self.lot_id = self.location_lot_line_id.lot_id
        else:
            self.lot_id = False

    @api.model
    def create(self, vals):
        import traceback
        traceback.print_stack()
        ret =super(StockPackOperationLot, self).create(vals)
        if ret.operation_id.picking_id.picking_type_id.code == 'incoming':
            if (ret.mrp or not vals.get('mrp')) == 0:
                raise UserError('Mrp is not set.')
            if (ret.sale_price ) == 0:
                raise UserError('Sale Price is not set.')
            if (ret.cost_price ) == 0:
                raise UserError('Cost Price is not set.')
            if not(ret.expiry_date ):
                raise UserError('Expiry Date is not set.')
        if ret.operation_id.picking_id:
            self.env['product.stock.picking'].create({
                                'picking_id': ret.operation_id.picking_id.id,
                                'product_id': ret.operation_id.product_id.id,
                                'product_uom_id' : ret.operation_id.product_uom_id.id,
                                'from_loc':ret.operation_id.from_loc,
                                'to_loc' :ret.operation_id.to_loc,
                                'lot_id' : ret.lot_id.id,
                                'qty_done' : ret.qty,
                                'stock_pack_operation_id' : ret.operation_id.id,
                                'stock_pack_operation_lot_id' :ret.id,
                                'available_qty' : ret.operation_id.available_qty,
                                'state' : ret.operation_id.picking_id.state
                                })
        return ret

    def write(self, vals):
        print(".................................222222222222222222222")
        ret =super(StockPackOperationLot, self).write(vals)
        if self.operation_id.picking_id.picking_type_id.code == 'incoming':
            if self.mrp == 0:
                raise UserError('Mrp is not set.')
            if self.sale_price == 0:
                raise UserError('Sale Price is not set.')
            if self.cost_price == 0:
                raise UserError('Cost Price is not set.')
            if not( self.expiry_date) : 
                raise UserError('Expiry Date is not set.')
        
        product_stock_picking_record = self.env['product.stock.picking'].search([('picking_id','=',self.operation_id.picking_id.id),('stock_pack_operation_lot_id','=',self.id)])
        if product_stock_picking_record:
            product_stock_picking_record.write({
                            'picking_id': self.operation_id.picking_id.id,
                            'product_id': self.operation_id.product_id.id,
                            'product_uom_id' : self.operation_id.product_uom_id.id,
                            'from_loc':self.operation_id.from_loc,
                            'to_loc' :self.operation_id.to_loc,
                            'lot_id' : self.lot_id.id,
                            'qty_done' : self.qty,
                            'stock_pack_operation_id' : self.operation_id.id,
                            'stock_pack_operation_lot_id' :self.id,
                            'available_qty' : self.operation_id.available_qty,
                            'state' : self.operation_id.picking_id.state
                                })
        return ret


