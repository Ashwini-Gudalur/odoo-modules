# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
import logging
from logging import getLogger
from datetime import datetime
_logger = getLogger(__name__)


class sale_order(models.Model):
    _inherit = "sale.order"
    
    invoice_ids = fields.Many2many("account.invoice", string='Invoices', compute="_get_invoiced", readonly=True, copy=False,store=True)
    # claimtype=fields.Selection([('1', 'Sickle Cell'), ('2', 'Bed Grant'),('3', 'CMCHIS')], 'Claim Type')
    claimtype = fields.Many2one("claim.type", string='Claim Type')

    # @api.depends('partner_id')
    # def _get_partner_claimtype_depends(self):
    #     res = {}
    #     for sale_order in self:
    #         partner_obj = self.env["res.partner"]
    #         partner = sale_order.partner_id
    #         partner_attri_cnt=self.env['res.partner.attributes'].search([('partner_id','=',partner.id)])
    #         if partner_attri_cnt:
    #             sale_order.claimtype = partner_attri_cnt.claimtype
    #         else:
    #             sale_order.claimtype=""
    #     return res

    # @api.onchange('partner_id','claimtype')
    # def _get_partner_claimtype(self):
    #     res = {}
    #     for sale_order in self:
    #         partner_obj = self.env["res.partner"]
    #         partner = sale_order.partner_id
    #         partner_attri_cnt=self.env['res.partner.attributes'].search([('partner_id','=',partner.id)])
    #         if partner_attri_cnt:
    #             sale_order.claimtype = partner_attri_cnt.claimtype.id
    #         else:
    #             sale_order.claimtype= False
    #     return res

    @api.multi
    @api.onchange('partner_caste')
    def _get_partner_attribute_details(self):
        res = {}
        for sale_order in self:
            partner_obj = self.env["res.partner"]
            partner = sale_order.partner_id
            partner_attri_cnt=self.env['res.partner.attributes'].search([('partner_id','=',partner.id)])
            if partner_attri_cnt:
                #partner_attribute=self.pool.get("res.partner.attributes").browse(cr,uid,partner_attri_cnt[0])
                #partner_attribute = 
                sale_order.partner_caste = partner_attri_cnt.x_Tribe
            else:
                sale_order.partner_caste=""
        return res

    @api.multi
    @api.onchange('partner_is_tribe')
    def _get_partner_attribute_Tribe_details(self):
        res = {}
        for sale_order in self:
            partner_obj = self.env["res.partner"]
            partner = sale_order.partner_id
            partner_attri_cnt=self.env['res.partner.attributes'].search([('partner_id','=',partner.id)])
            if partner_attri_cnt :
                #partner_attribute=self.pool.get("res.partner.attributes").browse(cr,uid,partner_attri_cnt[0])
                sale_order.partner_is_tribe = self.getYesOrNo(partner_attri_cnt.x_Is_Tribal)
            else:
                sale_order.partner_is_tribe =""
        return res
    
    @api.multi    
    @api.onchange('partner_is_sangam')
    def _get_partner_attribute_Sangam_details(self):
        res = {}
        for sale_order in self:
            partner_obj = self.env["res.partner"]
            partner = sale_order.partner_id
            partner_attri_cnt=self.env["res.partner.attributes"].search([('partner_id','=',partner.id)])
            if partner_attri_cnt:
                #partner_attribute=self.pool.get("res.partner.attributes").browse(cr,uid,partner_attri_cnt[0])
                sale_order.partner_is_sangam = self.getYesOrNo(partner_attri_cnt.x_Is_Sangam)
            else:
                sale_order.partner_is_sangam =""
        return res
        
    @api.multi    
    @api.onchange('partner_is_Premium')
    def _get_partner_attribute_Premium_details(self):
        res = {}
        for sale_order in self:
            partner_obj = self.env["res.partner"]
            partner = sale_order.partner_id
            partner_attri_cnt=self.env["res.partner.attributes"].search([('partner_id','=',partner.id)])
            if partner_attri_cnt:
                # partner_attribute=self.pool.get("res.partner.attributes").browse(cr,uid,partner_attri_cnt[0])
                sale_order.partner_is_Premium = self.getYesOrNo(partner_attri_cnt.x_Is_Premium_Paid)
            else:
                sale_order.partner_is_Premium=""
        return res
    
    @api.multi    
    @api.onchange('order_type')
    def _get_order_type(self):
        res = {}
        for sale_order in self:
            if (sale_order.shop_id):
                map_id_List = self.env['order.type.shop.map'].search([('shop_id', '=', sale_order.shop_id.id)])
                if(map_id_List):
                    # order_type_map = self.env['order.type.shop.map'].browse(map_id_List[0])
                    order_type_map = map_id_List[0] 
                    sale_order.order_type = order_type_map.order_type.name
                else:
                    sale_order.order_type =""
            else:
                sale_order.order_type =""
        return res
        
    @api.multi    
    @api.onchange('partner_visting')
    def _get_partner_attribute_Visiting(self):
        res = {}
        for sale_order in self:
            partner_obj = self.env["res.partner"]
            partner = sale_order.partner_id
            partner_attri_cnt=self.env["res.partner.attributes"].search([('partner_id','=',partner.id)])
            if partner_attri_cnt:
                #partner_attribute=self.pool.get("res.partner.attributes").browse(cr,uid,partner_attri_cnt[0])
                sale_order.partner_visting = partner_attri_cnt.x_Visiting
            else:
                sale_order.partner_visting=""
        return res
        
    def getYesOrNo(self, name):
        if(name):
            return 'Yes' if name.lower()=='True'.lower() else 'No'
        return ''

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(sale_order, self).onchange_partner_id()
        print("......",self)
        if self.partner_id:
            partner_attri_cnt=self.env["res.partner.attributes"].search([('partner_id','=',self.partner_id.id)])
            if partner_attri_cnt:
                #partner_attribute=self.pool.get("res.partner.attributes").browse(cr,uid,partner_attri_cnt[0])
                partner_attribute=partner_attri_cnt
                # res['value']['partner_caste'] = partner_attribute.x_Tribe
                # res['value']['partner_is_tribe'] = self.getYesOrNo(partner_attribute.x_Is_Tribal)
                # res['value']['partner_is_sangam'] = self.getYesOrNo(partner_attribute.x_Is_Sangam)
                # res['value']['partner_is_Premium'] = self.getYesOrNo(partner_attribute.x_Is_Premium_Paid)
                # res['value']['partner_visting'] = partner_attribute.x_Visiting

                self.partner_caste = partner_attribute.x_Tribe
                self.partner_is_tribe = self.getYesOrNo(partner_attribute.x_Is_Tribal)
                self.partner_is_sangam = self.getYesOrNo(partner_attribute.x_Is_Sangam)
                self.partner_is_Premium = self.getYesOrNo(partner_attribute.x_Is_Premium_Paid)
                self.partner_visting = partner_attribute.x_Visiting
                self.claimtype = partner_attribute.claimtype.id
            else:
                # res['value']['partner_caste'] = ''
                # res['value']['partner_is_tribe']= ''
                # res['value']['partner_is_sangam']= ''
                # res['value']['partner_is_Premium']= ''
                # res['value']['partner_visting']= ''
                self.partner_caste = ''
                self.partner_is_tribe = ''
                self.partner_is_sangam = ''
                self.partner_is_Premium = ''
                self.partner_visting = ''
                self.claimtype = False
            # claim_records=self.env["claim.type"].search([('erp_patient_id','=',self.partner_id.id)])
            # if claim_records:
            #     for record in  claim_records:
            #         self.claimtype = record.claim_type
            # self._get_partner_claimtype()
        return res 

    #purpose = fields.Char(compute='onchange_partner_id')
    #'partner_caste': fields.function(_get_partner_attribute_details, type='char', string ='Tribe'),
    #'order_type':fields.function(_get_order_type, type='char', string ='Order Type',),
    partner_caste = fields.Char(compute='_get_partner_attribute_details',string ='Tribe')
    partner_is_tribe=fields.Char(compute='_get_partner_attribute_Tribe_details', string ='Is Tribe')
    partner_is_sangam=fields.Char(compute='_get_partner_attribute_Sangam_details', string ='Is Sangam')
    partner_is_Premium=fields.Char(compute='_get_partner_attribute_Premium_details', string ='Is Premium')
    partner_visting=fields.Char(compute='_get_partner_attribute_Visiting', string ='Visiting')
    order_type =fields.Char(compute='_get_order_type', string ='Order Type')
    dateofAdmission = fields.Datetime('DoA')
    dateofDischarge = fields.Datetime('DoD')
    daysinhops =fields.Char(string ='Day in Hosp')


    @api.multi    
    @api.onchange('dateofAdmission','dateofDischarge')
    def on_change_dates(self):
        if self.dateofAdmission and self.dateofDischarge:
            t1=datetime.strptime(str(self.dateofAdmission),'%Y-%m-%d %H:%M:%S')
            t2=datetime.strptime(str(self.dateofDischarge),'%Y-%m-%d %H:%M:%S')
            t3=t2-t1
            self.daysinhops=str(t3)



    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(sale_order, self).action_invoice_create(grouped=False, final=False)
        invoices = self.env['account.invoice'].browse(res)
        for invoice in invoices:
            invoice.shop_id = self.shop_id.id
        return res


    # @api.onchange('shop_id')
    # def onchange_shop_id(self):
    #     self.warehouse_id = self.shop_id.warehouse_id.id
    #     self.location_id = self.shop_id.location_id.id
    #     self.payment_term_id = self.shop_id.payment_default_id.id
    #     self.project_id = self.shop_id.project_id.id if self.shop_id.project_id else False
    #     if self.shop_id.pricelist_id:
    #         self.pricelist_id = self.shop_id.pricelist_id.id
    #     if self.shop_id:
    #         return {'domain': {'order_line.lot_id': [('quant_ids.location_id', '=', self.shop_id.location_id.id),('quant_ids.qty', '>', 0)]}}
    #     else:
    #         return {'domain': {'order_line.lot_id': []}}
    #     return res

class res_partner_attributes(models.Model):
    
    _inherit = 'res.partner.attributes'
    
    partner_id =  fields.Many2one('res.partner', 'Partner', required=True, select=True, readonly=False )
    x_caste =  fields.Char('Caste',   required=False )
    x_class =  fields.Char('Class',   required=False )
    x_cluster =  fields.Char('Cluster',   required=False )
    x_patientcategory =  fields.Char('Staff Category', required=False )
    x_ContactNumber =  fields.Char('Contact Number',   required=False )
    x_debt =  fields.Char('Debt',   required=False )
    x_distanceFromCenter =  fields.Char('Distance From Center',   required=False )
    x_education =  fields.Char('Education',   required=False )
    x_familyIncome =  fields.Char('Family Income',   required=False )
    x_familyNameLocal =  fields.Char('Family Name Local',   required=False )
    x_givenNameLocal =  fields.Char('Given Name Local',   required=False )
    x_isUrban =  fields.Char('Is Urban', required=False )
    x_Is_Premium_Paid =  fields.Char('Is Premium Paid', required=False )
    x_Is_Sangam =  fields.Char('Is Sangam', required=False )
    x_Is_Tribal =  fields.Char('Is Tribal', required=False )
    x_landHolding =  fields.Char('Land Holding',   required=False )
    x_middleNameLocal =  fields.Char('Middle Name Local',   required=False )
    x_occupation =  fields.Char('Occupation',   required=False )
    x_primaryContact =  fields.Char('Primary Contact',   required=False )
    x_primaryRelative =  fields.Char('Primary Relative',   required=False )
    x_RationCard =  fields.Char('Ration Card',   required=False )
    x_secondaryContact =  fields.Char('Secondary Contact',   required=False )
    x_secondaryIdentifier =  fields.Char('Secondary Identifier',   required=False )
    x_Tribe =  fields.Char('Tribe',   required=False )
    x_Visiting =  fields.Char('Visiting',   required=False)
    # claimtype=fields.Selection([('1', 'Sickle Cell'), ('2', 'Bed Grant'),('3', 'CMCHIS')], 'Claim Type')
    claimtype = fields.Many2one("claim.type", string='Claim Type')

class res_partner(models.Model):
    _inherit = "res.partner"

    tin_number = fields.Char('TIN')

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

   
    @api.multi
    def _create_invoice(self, order, so_line, amount):
        '''Inherited this method to add values for fields,
         which are newly added to account_invoice class in customization'''
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes).ids
        else:
            tax_ids = taxes.ids
        invoice_values = {
                          'name': order.client_order_ref or order.name,
                          'origin': order.name,
                          'type': 'out_invoice',
                          'reference': False,
                          'account_id': order.partner_id.property_account_receivable_id.id,
                          'partner_id': order.partner_invoice_id.id,
                          'partner_shipping_id': order.partner_shipping_id.id,
                          'shop_id' : order.shop_id.id,
                          'invoice_line_ids': [(0, 0, {
                                                       'name': name,
                                                       'origin': order.name,
                                                       'account_id': account_id,
                                                       'price_unit': amount,
                                                       'quantity': 1.0,
                                                       'discount': 0.0,
                                                       'uom_id': self.product_id.uom_id.id,
                                                       'product_id': self.product_id.id,
                                                       'sale_line_ids': [(6, 0, [so_line.id])],
                                                       'invoice_line_tax_ids': [(6, 0, tax_ids)],
                                                       'account_analytic_id': order.project_id.id or False,
                                                       })],
                          'currency_id': order.pricelist_id.currency_id.id,
                          'payment_term_id': order.payment_term_id.id,
                          'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
                          'team_id': order.team_id.id,
                          'user_id': order.user_id.id,
                          'comment': order.note,
                          }
        invoice = inv_obj.create(invoice_values)
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',
                                       values={'self': invoice, 'origin': order},
                                       subtype_id=self.env.ref('mail.mt_note').id)
        return invoice





