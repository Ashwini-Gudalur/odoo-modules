# -*- coding: utf-8 -*-
from datetime import datetime
from pickle import FALSE

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    external_id = fields.Char(string="External ID",
                              help="This field is used to store encounter ID of bahmni api call")
    external_order_id = fields.Char(string="External Order ID",
                                    help="This field stores the order ID got from api call.")
    order_uuid = fields.Char(string="Order UUID",
                             help="Field for generating a random unique ID.")
    dispensed = fields.Boolean(string="Dispensed",
                               help="Flag to identify whether drug order is dispensed or not.")
    lot_id = fields.Many2one('stock.production.lot', string="Batch No")
    
    expiry_date = fields.Datetime(string="Expiry date")

    exempt_tax = fields.Boolean('Exempt Tax', default=False)
    # total_with_tax = fields.Float(compute="onchange_tax_id",string="Total With Tax",store=True)

    @api.onchange('exempt_tax')
    def onchange_exempt_tax(self):
        if self.exempt_tax:
            self.tax_id = [41]

    # @api.depends('tax_id','price_subtotal')
    # def onchange_tax_id(self):
    #     price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
    #     print(price,'price=====')
    #     taxes = self.tax_id.compute_all(price, self.order_id.currency_id, self.product_uom_qty, product=self.product_id,
    #                                     partner=self.order_id.partner_shipping_id)
    #     print(taxes,'taxes=====')
    #
    #     self.total_with_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])) + self.price_subtotal
    #     print(self.total_with_tax,'total_with_tax=====')



    @api.onchange('lot_id')
    def onchange_lot_id(self):
        if self.lot_id:
            self.expiry_date = self.lot_id.life_date
            if self.env.ref('bahmni_sale.sale_price_basedon_cost_price_markup').value == '1':
                self.price_unit = self.lot_id.sale_price if self.lot_id.sale_price > 0.0 else self.price_unit
        else:
            self.expiry_date = False

    @api.model
    def get_available_batch_details(self, product_id, sale_order):
        context = self._context.copy() or {}
        sale_order = self.env['sale.order'].browse(sale_order)
        context['location_id'] = sale_order.location_id and sale_order.location_id.id or False
        context['search_in_child'] = True
        stock_prod_lot = self.env['stock.production.lot']#.search([('product_id','=',product_id)])

        already_used_batch_ids = []
        for line in sale_order.order_line:
            if line.lot_id:
                id = line.lot_id.id
                already_used_batch_ids.append(id.__str__())

        query = ['&', ('product_id', '=', product_id), 
                 ('id', 'not in', already_used_batch_ids)]\
                 if len(already_used_batch_ids) > 0 else [('product_id','=',product_id)]
        for prodlot in stock_prod_lot.with_context(context).search(query,order='life_date asc'):
            if(prodlot.life_date and datetime.strptime(prodlot.life_date, DTF) >= datetime.today() and prodlot.stock_forecast > 0):
                return prodlot
        return None
    
    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).
 
        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 
                             'sale_line_ids': [(6, 0, [line.id])],
                             'cc': line.lot_id.id,
                             'lot_id':line.lot_id.id,
                             'batch_name':line.lot_id.name,
                             'expiry_date': line.expiry_date})
                self.env['account.invoice.line'].create(vals)




    # def lot_id_id_change(self):
    #     print("................................",self.product_id)
    #     print("................................",self.shop_id)
    #     if self.product_id and self.shop_id:
    #         records =self.env['stock.production.lot'].search([('product_id','=',self.product_id.id)])
    #         ids_list =[]
    #         for record in records:
    #             for line in record:
    #                 if line.location_id == self.shop_id.location_id and line.qty >0:
    #                     ids_list.append(record.id)
    #                     break
    #         print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #         print("................................",ids_list)
    #         print("................................",self.product_id)
    #         print("................................",self.shop_id)
    #         return {'domain': {'lot_id': [('id', 'in', tuple(ids_list))]}}
    #     else:
    #         return {'domain': {'lot_id': []}}
