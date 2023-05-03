# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime, date
from math import fabs
from pickle import FALSE
from lxml import etree

from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDF
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.osv.orm import setup_modifiers
from odoo.tools import pickle
import logging
_logger = logging.getLogger(__name__)



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total', 'discount', 'chargeable_amount','order_line.product_uom_qty')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            amount_total = amount_untaxed + amount_tax
            if order.chargeable_amount > 0.0:
                discount = amount_total - order.chargeable_amount
            else:
                discount = order.discount
            amount_total = amount_total - discount
            rounded_total =0
            round_off_value = 0
            if order.round_active:
                rounded_total = round(amount_total)
                round_off_value =  rounded_total - amount_total
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_total + round_off_value,
                'rounded_total': rounded_total,
                'total_outstanding_balance': order.prev_outstanding_balance + amount_total + round_off_value,
                'round_off_value':round_off_value
            })

    @api.depends('partner_id')
    def _calculate_balance(self):
        for order in self:
            order.prev_outstanding_balance = 0.0
            order.total_outstanding_balance = 0.0
            total_receivable = order._total_receivable()
            order.prev_outstanding_balance = total_receivable
            print("........prev_outstanding_balance",total_receivable)
    
    def _total_receivable(self):
        receivable = 0.0
        if self.partner_id:
            self._cr.execute("""SELECT l.partner_id, at.type, SUM(l.debit-l.credit) 
                          FROM account_move_line l
                          LEFT JOIN account_account a ON (l.account_id=a.id)
                          LEFT JOIN account_account_type at ON (a.user_type_id=at.id)
                          lEFT JOIN account_invoice ac on(ac.id = l.invoice_id)
                          WHERE at.type IN ('receivable','payable')
                          AND l.partner_id = %s
                          AND l.full_reconcile_id IS NULL
                          GROUP BY l.partner_id, at.type
                          """, (self.partner_id.id,))
            for pid, type, val in self._cr.fetchall():
                if val is None:
                    val=0
                receivable = (type == 'receivable') and val or -val

        return receivable

    @api.depends('partner_id')
    def _get_partner_details(self):
        for order in self:
            partner = order.partner_id
            order.update({
                'partner_uuid': partner.uuid,
                #'partner_village': partner.village,
            })


    partner_village = fields.Many2one("village.village", string="Partner Village")
    care_setting = fields.Selection([('ipd', 'IPD'),
                                     ('opd', 'OPD')], string="Care Setting")
    provider_name = fields.Char(string="Provider Name")
    discount_percentage = fields.Float(string="Discount Percentage")
    default_quantity = fields.Integer(string="Default Quantity")
    # above field is used to allow setting quantity as -1 in sale order line, when it is created through bahmni
    discount_type = fields.Selection([('none', 'No Discount'),
                                      ('fixed', 'Fixed'),
                                      ('percentage', 'Percentage')], string="Discount Type",
                                     default='none')
    discount = fields.Monetary(string="Discount")
    disc_acc_id = fields.Many2one('account.account', string="Discount Account Head")

    prev_outstanding_balance = fields.Monetary(string="Previous Outstanding Balance",
                                               compute=_calculate_balance)
    total_outstanding_balance = fields.Monetary(string="Total Outstanding Balance",
                                                compute=_amount_all)
    chargeable_amount = fields.Float(string="Chargeable Amount")
    # amount_round_off = fields.Float(string="Round Off Amount")
    round_off_value = fields.Float(compute='_amount_all', string='Round off amount')
    rounded_total = fields.Float(compute='_amount_all', string='Rounded Total')
    round_active = fields.Boolean(compute='get_round_active')




    def get_round_active(self):
        ir_values = self.env['ir.values']
        for i in self:
            i.round_active = ir_values.get_default('account.config.settings', 'round_off')
    # location to identify from which location order is placed.
    location_id = fields.Many2one('stock.location', string="Location")
    partner_uuid = fields.Char(string='Customer UUID', store=True, readonly=True, compute='_get_partner_details')
    shop_id = fields.Many2one('sale.shop', 'Shop', required=True)


    @api.onchange('order_line')
    def onchange_order_line(self):
        '''Calculate discount amount, when discount is entered in terms of %'''
        amount_total = self.amount_untaxed + self.amount_tax
        if self.discount_type == 'fixed':
            self.discount_percentage = 0
            # if self.discount >0 and amount_total >0:
            #     self.discount_percentage = self.discount/amount_total * 100
            if self.discount > amount_total :
                raise UserError(_('Discount Amount is more than Amount'))
        elif self.discount_type == 'percentage':
            self.discount = amount_total * self.discount_percentage / 100

        if self.discount_percentage > 100:
            raise UserError(_('Discount Percentage is more than 100....'))


    def write(self, vals):
        print(vals)
        res = super(SaleOrder, self).write(vals)
        amount_total = self.amount_untaxed + self.amount_tax
        if self.discount > amount_total :
            raise UserError(_('Discount Amount is more than Amount'))
        if self.discount_percentage > 100:
            raise UserError(_('Discount Percentage is more than 100....')) 
        return res
    
    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        amount_total = res.amount_untaxed + res.amount_tax
        if res.discount > amount_total :
            raise UserError(_('Discount Amount is more than Amount'))
        if res.discount_percentage > 100:
            raise UserError(_('Discount Percentage is more than 100....')) 
        return res
    
    @api.onchange('discount', 'discount_percentage', 'discount_type', 'chargeable_amount')
    def onchange_discount(self):
        self.onchange_order_line()
        amount_total = self.amount_untaxed + self.amount_tax
        # if self.chargeable_amount:
        #     if self.discount_type == 'none' and self.chargeable_amount:
        #         self.discount_type = 'fixed'
        #         discount = amount_total - self.chargeable_amount
        #         self.discount_percentage = (discount / amount_total) * 100
        # else:
        #     # if self.discount:
        #     #     self.discount_percentage = (self.discount / amount_total) * 100
        #     if self.discount_percentage:
        #         self.discount = amount_total * self.discount_percentage / 100
        
        if self.discount_type == 'fixed':
            # self.discount_percentage = (self.discount / amount_total) * 100
            self.discount_percentage = 0
            if self.discount > amount_total :
                raise UserError(_('Discount Amount is more than Amount'))
        elif self.discount_type == 'percentage':
            self.discount = amount_total * self.discount_percentage / 100
        else:
            self.discount = 0
            self.discount_percentage = 0
        if self.discount_percentage > 100:
            raise UserError(_('Discount Percentage is more than 100....'))
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        '''1. make percentage and discount field readonly, when chargeable amount is allowed to enter'''
        result = super(SaleOrder, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            group_id = self.env.ref("bahmni_sale.group_allow_change_so_charge").id
            doc = etree.XML(result['arch'])
            if group_id in self.env.user.groups_id.ids:
                for node in doc.xpath("//field[@name='discount_percentage']"):
                    node.set('readonly', '1')
                    setup_modifiers(node, result['fields']['discount_percentage'])
                for node in doc.xpath("//field[@name='discount']"):
                    node.set('readonly', '1')
                    setup_modifiers(node, result['fields']['discount'])
                for node in doc.xpath("//field[@name='discount_type']"):
                    node.set('readonly', '1')
                    setup_modifiers(node, result['fields']['discount_type'])
            result['arch'] = etree.tostring(doc)
        return result

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'discount_type': self.discount_type,
            'discount_percentage': self.discount_percentage,
            'disc_acc_id': self.disc_acc_id.id,
            'discount': self.discount,
        }
        return invoice_vals


    # By Pass the Invoice wizard while we press the "Create Invoice" button in sale order afer confirmation.
    # So Once we Confirm the sale order it will create the invoice and ask for the register payment.
    @api.multi
    def action_confirm(self):

        res = super(SaleOrder,self).action_confirm()
        self.validate_delivery()
        #here we need to set condition for if the its enabled then can continuw owise return True in else condition
        if self.env.user.has_group('bahmni_sale.group_skip_invoice_options'):
            for order in self:
                inv_data = order._prepare_invoice()
                created_invoice = self.env['account.invoice'].create(inv_data)
                print("......................................created_invoice",created_invoice.state)

                for line in order.order_line:
                    line.invoice_line_create(created_invoice.id, line.product_uom_qty)
                    
                # Use additional field helper function (for account extensions)
                for line in created_invoice.invoice_line_ids:
                    line._set_additional_fields(created_invoice)

                # Necessary to force computation of taxes. In account_invoice, they are triggered
                # by onchanges, which are not triggered when doing a create.
                created_invoice.compute_taxes()
                created_invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': created_invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
                created_invoice.action_invoice_open()#Validate Invoice
                ctx = dict(
                default_invoice_ids = [(4, created_invoice.id, None)]
                )
                print("......................................created_invoice",created_invoice.state)
                reg_pay_form = self.env.ref('account.view_account_payment_invoice_form')
                # self._cr.execute("""SELECT account_move_line.id,act.type,SUM(account_move_line.amount_residual) as amount                                      
                # FROM account_move_line
                # LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
                # LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                # WHERE act.type IN ('receivable')
                # AND account_move_line.partner_id= %s
                # and  act.type IN ('receivable','payable')
                # GROUP BY account_move_line.id,act.type
                #   HAVING SUM(account_move_line.amount_residual) !=0
                # """,created_invoice.partner_id.ids)
                # list=[]

                # for val in self._cr.fetchall():
                #     list.append(val[0])

                # if len(list) >1:
                #     records = self.env['account.move.line'].search([('id', 'in', tuple(list))])
                #     records.process_reconciliation(new_mv_line_dicts=[])
                # if created_invoice.state != 'paid':
                #     return {
                #         'name': _('Register Payment'),
                #         'type': 'ir.actions.act_window',
                #         'view_type': 'form',
                #         'view_mode': 'form',
                #         'res_model': 'account.payment',
                #         'views': [(reg_pay_form.id, 'form')],
                #         'view_id': reg_pay_form.id,
                #         'target': 'new',
                #         'context': ctx,
                #     }
                return {
                        'name': _('Register Payment'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'account.payment',
                        'views': [(reg_pay_form.id, 'form')],
                        'view_id': reg_pay_form.id,
                        'target': 'new',
                        'context': ctx,
                    }
        else:
            return res


    #This method will be called when validation is happens from the Bahmni side
    @api.multi
    def auto_validate_delivery(self):
        super(SaleOrder, self).action_confirm()
        self.validate_delivery()

    @api.multi
    def validate_delivery(self):
        if self.env.ref('bahmni_sale.validate_delivery_when_order_confirmed').value == '1':
            allow_negative = self.env.ref('bahmni_sale.allow_negative_stock')
            print("------------------------------------------------------------------------",self.picking_ids)
            if self.picking_ids:
                for picking in self.picking_ids:
                    if picking.state in ('waiting','confirmed','partially_available') and allow_negative.value == '1':
                        picking.force_assign()#Force Available
                    found_issue = False
                    if picking.state not in ('waiting','confirmed','partially_available'):
                        for pack in picking.pack_operation_product_ids:
                            pack_operation_lots = self.env['stock.pack.operation.lot'].search([('operation_id','=',pack.id)])
                            total_qty_done = 0
                            # self.env.cr.execute('ALTER TABLE stock_pack_operation_lot DROP INDEX stock_pack_operation_lot_uniq_lot_id')
                            # self.env.cr.execute('ALTER TABLE stock_pack_operation_lot DROP INDEX stock_pack_operation_lot_uniq_lot_name')
                            # for opration in pack_operation_lots:
                            #     self.env.cr.execute('update stock_pack_operation_lot set lot_id=NULL,lot_name=NULL WHERE operation_id=%s', (opration.id,))
                            operation_link_obj = self.env['stock.move.operation.link'].search([('operation_id','=',pack.id)],limit=1)
                            move_obj = operation_link_obj.move_id
                            for pack_operation_lot in pack_operation_lots:
                                qty_done = 0
                                if pack.product_id.tracking != 'none':
                                    line = self.order_line.filtered(lambda l:l.product_id == pack.product_id and l.lot_id.id == pack_operation_lot.lot_id.id)
                                    # line = operation_link_obj.move_id.procurement_id.sale_line_id
                        
                                    lot_ids = None
                                    if line.lot_id:
                                        lot_ids = line.lot_id
                                    else:
                                        lot_ids = self._find_batch(pack.product_id,pack.product_qty,pack.location_id,picking)
                                   
                                    if lot_ids:
                                        # #First need to Find the related move_id of this operation
                                        # operation_link_obj = self.env['stock.move.operation.link'].search([('operation_id','=',pack.id)],limit=1)
                                        # move_obj = operation_link_obj.move_id
                                    
                                        for lot in lot_ids:
                                            print("------------------------0000")
                                            pack_operation_lot.write({
                                                'lot_name': lot.name,
                                                'qty': line.product_uom_qty,
                                                'operation_id': pack.id,
                                                'move_id': move_obj.id,
                                                'lot_id': lot.id,
                                                'cost_price': lot.cost_price,
                                                'sale_price': lot.sale_price,
                                                'mrp': lot.mrp
                                                })
                            
                                        qty_done = qty_done + line.product_uom_qty
                                        total_qty_done = total_qty_done + qty_done
                                    else:
                                        found_issue = True
                                else:
                                    print("....................................................",pack)
                                    pack.qty_done = pack.product_qty
                            pack.qty_done = total_qty_done
                        if not found_issue:
                            picking.do_new_transfer()#Validate
                    else:
                        message = ("<b>Auto validation Failed</b> <br/> <b>Reason:</b> There are not enough stock available for Some product on <a href=# data-oe-model=stock.location data-oe-id=%d>%s</a> Location") % (self.location_id,self.location_id.name)
                        self.message_post(body=message)

    def _find_batch(self, product, qty, location, picking):
        _logger.info("\n\n***** Product :%s, Quantity :%s Location :%s\n*****",product,qty,location)
        lot_objs = self.env['stock.production.lot'].search([('product_id','=',product.id),('life_date','>=',str(fields.datetime.now()))])
        _logger.info('\n *** Searched Lot Objects:%s \n',lot_objs)
        if any(lot_objs):
            #Sort losts based on the expiry date FEFO(First Expiry First Out)
            lot_objs = list(lot_objs)
            sorted_lot_list = sorted(lot_objs, key=lambda l: l.life_date)
            _logger.info('\n *** Sorted based on FEFO :%s \n',sorted_lot_list)
            done_qty = qty
            res_lot_ids = []
            lot_ids_for_query = tuple([lot.id for lot in sorted_lot_list])
            self._cr.execute("SELECT SUM(qty) FROM stock_quant WHERE lot_id IN %s and location_id=%s",(lot_ids_for_query,location.id,))
            qry_rslt = self._cr.fetchall()
            available_qty = qry_rslt[0] and qry_rslt[0][0] or 0
            if available_qty >= qty:
                for lot_obj in sorted_lot_list:
                    quants = lot_obj.quant_ids.filtered(lambda q: q.location_id == location)
                    for quant in quants:
                        if done_qty >= 0:
                            res_lot_ids.append(lot_obj)
                            done_qty = done_qty - quant.qty
                return res_lot_ids
            else:
                message = ("<b>Auto validation Failed</b> <br/> <b>Reason:</b> There are not enough stock available for <a href=# data-oe-model=product.product data-oe-id=%d>%s</a> product on <a href=# data-oe-model=stock.location data-oe-id=%d>%s</a> Location") % (product.id,product.name,location.id,location.name)
                self.message_post(body=message)
        else:
            message = ("<b>Auto validation Failed</b> <br/> <b>Reason:</b> There are no Batches/Serial no's available for <a href=# data-oe-model=product.product data-oe-id=%d>%s</a> product") % (product.id,product.name)
            self.message_post(body=message)
            return False
       
    @api.onchange('shop_id')
    def onchange_shop_id(self):
        self.warehouse_id = self.shop_id.warehouse_id.id
        self.location_id = self.shop_id.location_id.id
        self.payment_term_id = self.shop_id.payment_default_id.id
        self.project_id = self.shop_id.project_id.id if self.shop_id.project_id else False
        if self.shop_id.pricelist_id:
            self.pricelist_id = self.shop_id.pricelist_id.id
            
    @api.multi
    def validate_payment(self):
        for obj in self:
            ctx = {'active_ids': [obj.id]}
            default_vals = self.env['sale.advance.payment.inv'
                                        ].with_context(ctx).default_get(['count', 'deposit_taxes_id',
                                                                         'advance_payment_method', 'product_id',
                                                                         'deposit_account_id'])
            payment_inv_wiz = self.env['sale.advance.payment.inv'].with_context(ctx).create(default_vals)
            payment_inv_wiz.with_context(ctx).create_invoices()
            for inv in obj.invoice_ids:
                inv.action_invoice_open()
                if inv.state == 'paid':
                    continue
                elif inv.amount_total > 0:
                    account_payment_env = self.env['account.payment']
                    fields = account_payment_env.fields_get().keys()
                    default_fields = account_payment_env.with_context({'default_invoice_ids': [(4, inv.id, None)]}).default_get(fields)
                    journal_id = self.env['account.journal'].search([('type', '=', 'cash')],
                                                                    limit=1)
                    default_fields.update({'journal_id': journal_id.id})
                    payment_method_ids = self.env['account.payment.method'
                                                  ].search([('payment_type', '=', default_fields.get('payment_type'))]).ids
                    if default_fields.get('payment_type') == 'inbound':
                        journal_payment_methods = journal_id.inbound_payment_method_ids.ids
                    elif default_fields.get('payment_type') == 'outbound':
                        journal_payment_methods = journal_id.outbound_payment_method_ids.ids
                    common_payment_method = list(set(payment_method_ids).intersection(set(journal_payment_methods)))
                    common_payment_method.sort()
                    default_fields.update({'payment_method_id': common_payment_method[0]})
                    account_payment = account_payment_env.create(default_fields)
                    account_payment.post()
                else:
                    message = "<b>Auto validation Failed</b> <br/> <b>Reason:</b> The Total amount is 0 So, Can't Register Payment."
                    inv.message_post(body=message)


class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"


    def get_payment_vals(self):
        shop_id= False
        for inv in self._get_invoices():
            if inv.shop_id:
                shop_id = inv.shop_id
                break
        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'invoice_ids': [(4, inv.id, None) for inv in self._get_invoices()],
            'shop_id':shop_id.id,
            'payment_type': self.payment_type,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': self.partner_type,
        }
    @api.multi
    def create_payment(self):
        payment = self.env['account.payment'].create(self.get_payment_vals())
        payment.post()
        return {'type': 'ir.actions.act_window_close'}
