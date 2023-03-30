# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
import logging
from logging import getLogger
_logger = getLogger(__name__)

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = "res.partner"

    tin_number=fields.Char(string='TIN')
    

# class stock_move_split_lines_exten(models.TransientModel):

#     _inherit = "stock.move.split.lines"

#     def _get_product_mrp(self, cr, uid, context=None):
#         context = context or {}
#         tax_amount = 0
#         stock_move_id = context.get('stock_move', None)
#         stock_move = stock_move_id and self.pool.get('stock.move').browse(cr, uid, stock_move_id, context=context)
#         return (stock_move and stock_move.purchase_line_id and stock_move.purchase_line_id.mrp) or 0.0

#     def onchange_cost_price(self, cr, uid, ids, cost_price, context=None):
#         cost_price = cost_price or 0.0
#         product_uom = self._get_product_uom(cr, uid, context=context)
#         mrp = self._get_product_mrp(cr, uid, context=context)
#         return {'value': {'sale_price': self._calculate_sale_price(cr,uid,cost_price, product_uom,mrp)}}

#     def _calculate_sale_price(self, cr,uid,cost_price, product_uom, mrp):
#         cost_price = cost_price or 0.0
#         product_uom_factor = product_uom.factor if(product_uom is not None) else 1.0
#         cost_price_per_unit = cost_price * product_uom_factor
#         margin_percent = 200.0
#         sp_incl_tax = cost_price + (cost_price * 2)
#         default_tax_percent = self.pool.get('ir.values').get_default(cr, uid, 'sale.config.settings', 'default_tax_percent')
#         #Assuming 5% tax
#         if(mrp>0.0 and sp_incl_tax>mrp):
#             sp_incl_tax = mrp
#         if(default_tax_percent>0):
#             divisor = 1+(default_tax_percent/100)
#             actual_sp = sp_incl_tax/divisor
#         else:
#             actual_sp = sp_incl_tax
#             #remove the rounding...
#         actual_sp = actual_sp - 0.01
#         return actual_sp

#     def _calculate_default_sale_price(self, cr, uid, context=None):
#         cost_price = self._get_default_cost_price(cr, uid, context=context) or 0.0
#         product_uom = self._get_product_uom(cr, uid, context=context)
#         mrp = self._get_product_mrp(cr, uid, context=context)
#         return self._calculate_sale_price(cr,uid,cost_price, product_uom,mrp)

#     name=fields.Char('Batch Number', size=64)
#     prodlot_id=fields.Many2one('stock.production.lot', 'Batch Number')
        
#     _defaults = {
#         'mrp': _get_product_mrp,
#         'sale_price': _calculate_default_sale_price
#     }

# stock_move_split_lines_exten()


# class split_in_production_lot_with_price_exten(models.TransientModel):
#     _name = "stock.move.split"
#     _inherit = "stock.move.split"
#     _description = "Split in Batch Numbers"

#     def split(self, cr, uid, ids, move_ids, context=None):
#         """ To split stock moves into serial numbers
#         :param move_ids: the ID or list of IDs of stock move we want to split
#         """
#         if context is None:
#             context = {}
#         assert context.get('active_model') == 'stock.move', \
#             'Incorrect use of the stock move split wizard'
#         move_obj = self.pool.get('stock.move')
#         for data in self.browse(cr, uid, ids, context=context):
#             for move in move_obj.browse(cr, uid, move_ids, context=context):
#                 move_qty = move.product_qty
#                 quantity_rest = move.product_qty
#                 uos_qty_rest = move.product_uos_qty
#                 new_move = []
#                 if data.use_exist:
#                     lines = [l for l in data.line_exist_ids if l]
#                 else:
#                     lines = [l for l in data.line_ids if l]
#                 total_move_qty = 0.0
#                 default_tax_percent = self.pool.get('ir.values').get_default(cr, uid, 'sale.config.settings', 'default_tax_percent')
#                 for line in lines:
#                     _logger.error("line = %s",line)
#                     sp_with_tax = line.sale_price +((default_tax_percent/100)*line.sale_price)
#                     if sp_with_tax>line.mrp :
#                         raise osv.except_osv(_('Processing Error!'), _('Batch number %s of %s has : Sales Price + Tax more that mrp :(%f+5%%) %f > %f)!') \
#                                              % (line.name, move.product_id.name, line.sale_price, sp_with_tax, line.mrp))

#                     _logger.error("EXP DATE=%s",line.expiry_date)
#                     if (line.expiry_date):
#                         if (datetime.strptime(line.expiry_date,'%Y-%m-%d') <= datetime.today()):
#                             raise osv.except_osv(_('Processing Error!'), _('End of life should be greater than today'))
#         return super(split_in_production_lot_with_price_exten, self).split(cr, uid, ids, move_ids, context)



class stock_production_lot(models.Model):

    # _name = 'stock.production.lot'
    _inherit = 'stock.production.lot'

    def write(self, cr, uid, ids, values, context=None):
        sales_price = values.get('sale_price')
        mrp = values.get('mrp')
        life_date = values.get('life_date')
        _logger.error("Values  = %s",values)
        _logger.error("Life date = %s",ids)
        default_tax_percent = self.pool.get('ir.values').get_default(cr, uid, 'sale.config.settings', 'default_tax_percent')
        if not mrp and len(ids)>0:
            old = self.browse(cr, uid, ids, context=context)
            _logger.error("old=%s",old)
            if(len(old)>0):
                old=old[0]
                mrp=old['mrp']
                _logger.error("Values  = %s",mrp)
        if not life_date and len(ids)>0:
            old = self.browse(cr, uid, ids,  context=context)
            if(len(old)>0):
                life_date=old[0]['life_date']
                life_date=datetime.strptime(life_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
                life_date = life_date.strftime('%Y-%m-%d')
                _logger.error("Values  = %s",life_date)
        if sales_price and mrp:
            sp_incl_tax = sales_price + (sales_price * (default_tax_percent/100))
            #Assuming 5% tax
            _logger.error("Default Tax Percent = %s",default_tax_percent)
            _logger.error("Sales Price = %s",(sales_price * (default_tax_percent/100)))

            if(sp_incl_tax>mrp):
                raise osv.except_osv(_('Processing Error!'), _('Batch number has : Sales Price + Tax more that mrp :(%f+5%%) %f > %f)!') \
                                     % (sales_price, sp_incl_tax, mrp))
        if(life_date):
            if (datetime.strptime(life_date,'%Y-%m-%d') <= datetime.today()):
                raise osv.except_osv(_('Processing Error!'), _('End of life should be greater than today'))
        else:
            if context is not None:
                raise osv.except_osv(_('Processing Error!'), _('End of life date is a mandatory field'))
        return super(stock_production_lot, self).write(cr, uid, ids, values, context)

    def create(self, cr, uid, values, context=None):
        sales_price = values.get('sale_price')
        mrp = values.get('mrp')
        default_tax_percent = self.pool.get('ir.values').get_default(cr, uid, 'sale.config.settings', 'default_tax_percent')
        if sales_price and mrp:
            sp_incl_tax = sales_price + (sales_price * (default_tax_percent/100))
            #Assuming 5% tax
            _logger.error("Default Tax Percent = %s",default_tax_percent)
            _logger.error("Sales Price = %s",(sales_price * (default_tax_percent/100)))
            if(sp_incl_tax>mrp):
                raise osv.except_osv(_('Processing Error!'), _('Batch number has : Sales Price + Tax more that mrp :(%f+5%%) %f > %f)!') \
                                     % (sales_price, sp_incl_tax, mrp))
        return super(stock_production_lot, self).create(cr, uid, values, context)

        sale_price =fields.Float('Sale Price',digits=(4,2))
        mrp = fields.Float('MRP',digits=(4,2))
        cost_price = fields.Float('Cost Price',digits=(4,2))
        name = fields.Char('Batch Number')
            

    def _get_locationForshop(self, cr, uid, shop_id, context=None):
        shop_obj = self.pool.get('sale.shop')
        shop = shop_obj.browse(cr, uid, shop_id)
        if(not shop_id):
            return 0
        if shop:
            location_id = shop.warehouse_id and shop.warehouse_id.lot_stock_id.id
            if location_id:
                return location_id
        return 0

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        args = args or []
        ids = []
        _logger.error("Only available %s",context.get('only_available_batch', False))
        _logger.error("location id = %s",context.get('location_id', False))
        if(context.get('only_available_batch', False)):
            batch_stock_query = 'select prodlot_id from batch_stock_future_forecast where qty > 0'
            for column,operator,value in args:
                if(column == "product_id"):
                    batch_stock_query += " and product_id = %s" % value
            if context.get('location_id', False):
                batch_stock_query += " and location_id = %s" % context['location_id']
            elif context.get('shop',False) :
                shop = self._get_locationForshop(cr,uid,context.get('shop',False))
                if shop>0 :
                    batch_stock_query += " and location_id = %s" % shop
            self.env.cr.execute(batch_stock_query)
            args += [('id', 'in', [row[0] for row in self.env.cr.fetchall()])]

        if name:
            ids = self.search(cr, uid, [('prefix', '=', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', 'ilike', name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)


class custom_sale_configuration(models.TransientModel):
    _inherit = 'sale.config.settings'

    group_final_so_charge = fields.Boolean('Allow to enter final Sale Order Charge',
                                            implied_group='bahmni_sale_discount.group_final_so_charge')
    group_default_quantity = fields.Boolean('Allow to enter default drug Quantity as -1',
                                                implied_group='bahmni_sale_discount.group_default_quantity')
    default_tax_percent = fields.Integer("Percentage of Tax which need to be used for calculating sales price of a product based on cost. This should be equal to sales tax.. (or combination of sales taxes) Used in product receive screen to calculate SP",default=5)
        

    

    def default_get(self, fields):
        return super(custom_sale_configuration, self).default_get(fields)

    def set_default_tax_percent(self):
        ir_values = self.env['ir.values']
        config = self.browse(self.ids)
        ir_values.set_default('sale.config.settings', 'default_tax_percent', config.default_tax_percent)


