# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api , _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import Warning


class StockPackOperationLot(models.Model):
    _inherit = 'stock.pack.operation.lot'

    @api.model
    def default_get(self, fields):
        res = {}
        ctx = self._context.copy()
        operation_id = ctx.get('operation_id')
        # get cost price of product from purchase order line, linked with stock_move
        if operation_id:
            pack_operation = self.env['stock.pack.operation'].browse(operation_id)
            mv_op_link_ids = self.env['stock.move.operation.link'].search([('operation_id', '=', operation_id)],limit=1)
            if pack_operation.check_operation:
                res.update({'check_operation_lot': True})
            if mv_op_link_ids:
                for link in mv_op_link_ids:
                    res.update({'move_id': link.move_id.id})
                    purchase_line = link.move_id.purchase_line_id
                    amount_tax = 0.0
                    if pack_operation.picking_id.company_id.tax_calculation_rounding_method == 'round_globally':
                        taxes = purchase_line.taxes_id.compute_all(purchase_line.price_unit, purchase_line.order_id.currency_id,
                                                                   1.0, pack_operation.product_id, pack_operation.picking_id.partner_id)
                        amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    else:
                        amount_tax += purchase_line.price_tax
                    if purchase_line.price_unit + amount_tax > 0:
                        res.update({'cost_price': purchase_line.price_unit + amount_tax})
                    if purchase_line.mrp > 0:
                        res.update({'mrp':purchase_line.mrp})
                    # res.update({'cost_price': purchase_line.price_unit + amount_tax,'mrp':purchase_line.mrp})
        # calculate sale price, based on markup percentage defined in price markup table
        if res.get('cost_price'):
            cost_price = res.get('cost_price')
            markup_table_line = self.env['price.markup.table'].search([('lower_price', '<', cost_price),
                                                                       '|', ('higher_price', '>=', cost_price),
                                                                       ('higher_price', '=', 0)])
            if markup_table_line and len(markup_table_line)==1:
                if cost_price + (cost_price * markup_table_line.markup_percentage / 100) > 0:
                    res.update({'sale_price': cost_price + (cost_price * markup_table_line.markup_percentage / 100)})
                # res.update({'sale_price': cost_price + (cost_price * markup_table_line.markup_percentage / 100)})

            print("..................res............,res",res)
        return res

    sale_price = fields.Float(string="Sale Price", digits=dp.get_precision('Product Price'))
    cost_price = fields.Float(string="Cost Price", digits=dp.get_precision('Product Price'))
    mrp = fields.Float(string="MRP", digits=dp.get_precision('Product Price'))
    expiry_date = fields.Datetime(string="Expiry Date", digits=dp.get_precision('Product Price'))
    move_id = fields.Many2one('stock.move',
                              string="Stock Move",
                              help="This field is used to track, which all move_ids are utilized to fetch cost_price")
    check_operation_lot = fields.Boolean( string='Check',default=False)
    location_lot_line_id = fields.Many2one('location.stock.quant', string="Lot/serialNumber")

    @api.onchange('location_lot_line_id')
    def onchange_location_lot_line_id(self):
        if self.location_lot_line_id:
            self.lot_id = self.location_lot_line_id.lot_id
        else:
            self.lot_id = False



    @api.onchange('lot_id')
    def onchange_lot_id(self):
        for record in self:
            if record.lot_id:
                if record.lot_id.mrp > 0:
                    record.mrp = record.lot_id.mrp
                if record.lot_id.sale_price > 0:
                    record.sale_price = record.lot_id.sale_price
                if record.lot_id.cost_price >0:
                    record.cost_price = record.lot_id.cost_price
                if record.lot_id.life_date:
                    record.expiry_date = record.lot_id.life_date


    # @api.onchange('cost_price','mrp','sale_price')
    @api.onchange('cost_price','mrp')
    def onchange_cost_price(self):
        for record in self:
            if record.cost_price:
                markup_table_line = self.env['price.markup.table'].search([('lower_price', '<', record.cost_price),
                                                                       '|', ('higher_price', '>=', record.cost_price),
                                                                       ('higher_price', '=', 0)])
                if markup_table_line and len(markup_table_line)==1:
                    self.sale_price =  record.cost_price + (record.cost_price * markup_table_line.markup_percentage / 100)

                if record.sale_price > 0 and record.mrp >0:
                    
                    if record.lot_id:
                        if record.lot_id.sale_price >0:
                            record.sale_price = record.lot_id.sale_price
                        if record.sale_price > record.mrp :
                            record.sale_price = record.mrp
                    else:
                        if record.sale_price > record.mrp :
                            record.sale_price = record.mrp
            else:
                if record.sale_price > record.mrp :
                    record.sale_price = record.mrp
                # default_tax_percent = self.env['ir.values'].get_default('sale.config.settings', 'default_tax_percent')
                # if default_tax_percent:
                #     sp_with_tax = record.sale_price +((default_tax_percent/100)*record.sale_price)
                # else:
                #     sp_with_tax = record.sale_price
                # if sp_with_tax>record.mrp :
                #     raise Warning ('Batch number %s  : Sales Price + Tax more that mrp :(%f+5%%) %f > %f)!' \
                #                             % (record.lot_id.name, record.sale_price, sp_with_tax, record.mrp))
    
    @api.onchange('sale_price')
    def onchange_sale_price(self):
        if self.lot_id:
            if self.lot_id.sale_price >0:
                self.sale_price = self.lot_id.sale_price
                if self.sale_price > self.mrp :
                    self.sale_price = self.mrp
            else:
                if self.sale_price > 0 and self.mrp >0:
                    if self.sale_price > self.mrp :
                        self.sale_price = self.mrp
    
    @api.model
    def create(self, vals):
        default_tax_percent = self.env['ir.values'].get_default('sale.config.settings', 'default_tax_percent')
        sale_price = vals.get('sale_price')
        mrp = vals.get('mrp')
        if default_tax_percent:
            sp_with_tax = sale_price +((default_tax_percent/100)*sale_price)
        else:
            sp_with_tax = sale_price
        if sp_with_tax>mrp :
            raise UserError('Batch number : Sales Price + Tax more that mrp :(%f+5%%) %f > %f)!' \
                                    % (sale_price, sp_with_tax, mrp))
        return super(StockPackOperationLot, self).create(vals)

    @api.multi
    def write(self, vals):
        default_tax_percent = self.env['ir.values'].get_default('sale.config.settings', 'default_tax_percent')
        sale_price = vals.get('sale_price') or self.sale_price
        mrp = vals.get('mrp') or self.mrp
        if default_tax_percent:
            sp_with_tax = sale_price +((default_tax_percent/100)*sale_price)
        else:
            sp_with_tax = sale_price
        if sp_with_tax>mrp :
            raise UserError('Batch number : Sales Price + Tax more that mrp :(%f+5%%) %f > %f)!' \
                                    % (sale_price, sp_with_tax, mrp))
        return super(StockPackOperationLot, self).write(vals)
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    check = fields.Boolean(string='Check')

class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    check_operation = fields.Boolean(related='picking_id.check', string='Check')


    @api.multi
    def action_split_lots(self):
        action_ctx = dict(self.env.context)
        # If it's a returned stock move, we do not want to create a lot
        returned_move = self.linked_move_operation_ids.mapped('move_id').mapped('origin_returned_move_id')
        picking_type = self.picking_id.picking_type_id
        action_ctx.update({
            'check':self.check_operation,
            'serial': self.product_id.tracking == 'serial',
            'only_create': picking_type.use_create_lots and not picking_type.use_existing_lots and not returned_move,
            'create_lots': picking_type.use_create_lots,
            'state_done': self.picking_id.state == 'done',
            'show_reserved': any([lot for lot in self.pack_lot_ids if lot.qty_todo > 0.0])})
        view_id = self.env.ref('stock.view_pack_operation_lot_form').id
        return {
            'name': _('Lot/Serial Number Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.pack.operation',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx}
    split_lot = action_split_lots


