# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

logger = logging.getLogger(__name__)

class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    available_qty = fields.Integer(string="Available Qty")
    picking_type = fields.Char(string="Operation Type")
    # existing_lot = fields.Boolean(string="Existing Lot/serial Number")

    @api.multi
    def save(self):
        import traceback
        traceback.print_stack()
        '''This method is overridden to restrict user from assigning expired lots'''
        # TDE FIXME: does not seem to be used -> actually, it does
        # TDE FIXME: move me somewhere else, because the return indicated a wizard, in pack op, it is quite strange
        # HINT: 4. How to manage lots of identical products?
        # Create a picking and click on the Mark as TODO button to display the Lot Split icon. A window will pop-up. Click on Add an item and fill in the serial numbers and click on save button
        for pack in self:
            if pack.product_id.tracking != 'none':
                #mrp = pack.linked_move_operation_ids[0].move_id.purchase_line_id.mrp
                #unit_price = pack.linked_move_operation_ids[0].move_id.purchase_line_id.price_unit
                for lot in pack.pack_lot_ids:
                    if lot.expiry_date and lot.lot_id:
                        lot.lot_id.life_date = lot.expiry_date
                        lot.lot_id.use_date = lot.expiry_date
                        if lot.mrp > 0:
                            lot.lot_id.mrp = lot.mrp
                        else:
                            if lot.mrp == 0:
                               lot.mrp = lot.lot_id.mrp 

                        if lot.sale_price >0:
                            lot.lot_id.sale_price = lot.sale_price
                        else:
                            if lot.sale_price == 0:
                               lot.sale_price = lot.lot_id.sale_price
                        if lot.cost_price>0:
                            lot.lot_id.cost_price = lot.cost_price
                        else:
                            if lot.cost_price == 0:
                               lot.cost_price = lot.lot_id.cost_price
                    #lot.lot_id.mrp = mrp
                    #lot.lot_id.cost_price = unit_price
                    #lot.lot_id.sale_price = unit_price
                    #life_date = datetime.strptime(lot.lot_id.life_date, DTF)
                    #if life_date < datetime.today():
                        #raise Warning("Lot %s is expired, you can process expired lot!"%(lot.lot_id.name))
                pack.write({'qty_done': sum(pack.pack_lot_ids.mapped('qty'))})
        return {'type': 'ir.actions.act_window_close'}

    # @api.model
    # def create(self, vals):
    #     ret = super(StockPackOperation, self).create(vals)
    #     if ret.product_id.tracking == 'none':
    #         self.env['product.stock.picking'].create({
    #                             'picking_id': ret.picking_id.id,
    #                             'product_id': ret.product_id.id,
    #                             'product_uom_id' : ret.product_uom_id.id,
    #                             'from_loc':ret.from_loc,
    #                             'to_loc' :ret.to_loc,
    #                             'lot_id' : False,
    #                             'qty_done' : ret.qty_done,
    #                             'stock_pack_operation_id' : ret.id,
    #                             'stock_pack_operation_lot_id' :False,
    #                             'available_qty' : ret.available_qty,
    #                             'state' : ret.state
    #                             })
    #     return ret

    # def write(self, vals):
    #     ret = super(StockPackOperation, self).write(vals)
    #     if self.product_id.tracking == 'none':
    #         product_stock_picking = self.env['product.stock.picking'].search([('stock_pack_operation_id', '=', self.id)])
    #         if product_stock_picking:
    #             product_stock_picking.write({
    #                                 'picking_id': self.picking_id.id,
    #                                 'product_id': self.product_id.id,
    #                                 'product_uom_id' : self.product_uom_id.id,
    #                                 'from_loc':self.from_loc,
    #                                 'to_loc' :self.to_loc,
    #                                 'lot_id' : False,
    #                                 'qty_done' : self.qty_done,
    #                                 'stock_pack_operation_id' : self.id,
    #                                 'stock_pack_operation_lot_id' :False,
    #                                 'available_qty' : self.available_qty,
    #                                 'state' : self.state
    #                                 })
    #     return ret

class StockPackOperationLot(models.Model):
    _inherit = 'stock.pack.operation.lot'

    available_qty = fields.Integer(string="Available Qty")

    
    # location_lot_line_id = fields.Many2one('location.stock.quant', string="Lot/serial Number")

    # @api.onchange('location_lot_line_id')
    # def onchange_location_lot_line_id(self):
    #     if self.location_lot_line_id:
    #         self.lot_id = self.location_lot_line_id.lot_id
    #     else:
    #         self.lot_id = False
    
    #@api.onchange('lot_id')
    #def onchange_lot_id(self):
        #if self.lot_id:
            #if self.lot_id.life_date:
                #lot_life_date = datetime.strptime(self.lot_id.life_date, DTF)
                #if lot_life_date < datetime.today():
                    #self.expiry_date = self.lot_id.life_date
                    #warning = {'name': 'Lot Expired',
                               #'message': "This lot is already expired!"}
                    #return {'warning': warning}
            #self.available_qty = self.env['product.product'].with_context({'location': self.operation_id.location_id.id,
            #'lot_id': self.lot_id.id}).browse(self.operation_id.product_id.id).qty_available
            #self.expiry_date = self.lot_id.life_date
            
