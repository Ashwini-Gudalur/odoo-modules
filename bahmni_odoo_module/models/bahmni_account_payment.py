# -*- coding: utf-8 -*-
from itertools import groupby
from odoo import models, fields, api
from odoo.exceptions import Warning
import logging
import pytz
from dateutil import parser, tz
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from numtoword import convertToWords

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'
     
     
    # @api.multi
    # def get_invoice_lines(self):
    #     print('%%%%%%%%%%%%%%%%%%%%%%')
    #     provider_name = []
    #     taxes = 0.0
    #     amount_untaxed = 0.0
    #     discount = 0.0
    #     round_off=0.0
    #     bill_amount = 0.0
    #     invoice_data = {'taxes': 0.0,
    #                     'amount_untaxed': 0.0,
    #                     'discount': 0.0,
    #                     'net_amount': 0.0,
    #                     'previous_balance': 0.0,
    #                     'bill_amount': 0.0,
    #                     'paid_amount': 0.0,
    #                     'outstanding_balance': 0.0,
    #                     'round_off_value':0.0
    #                     }
    #     invoice_lines = []
    #     for inv in self.invoice_ids:
    #         sale_order = self.env['sale.order'].search([('name', '=', inv.origin)])
    #         if sale_order.provider_name:
    #             provider_name.append(sale_order.provider_name)
    #         taxes += inv.amount_tax
    #         amount_untaxed += inv.amount_untaxed
    #         round_off+=inv.round_off_value
    #         discount += inv.discount
    #         bill_amount += inv.amount_total
    #         for line in inv.invoice_line_ids:
    #             tax_code = ''
    #             if line.invoice_line_tax_ids:
    #                     for tax_name in line.invoice_line_tax_ids:
    #                         tax_code+=tax_name.name
    #             invoice_lines.append({'product_name': line.product_id.name,
    #                                   'expiry_date': line.expiry_date,
    #                                   'quantity': line.quantity,
    #                                   'price_unit': line.price_unit,
    #                                   'tax_code':tax_code,
    #                                   'taxes':0,
    #                                   'batch_name':line.lot_id and line.lot_id.name or '',
    #                                   'price_subtotal': line.price_subtotal})
    #     invoice_data['invoice_lines'] = invoice_lines
    #     print(".........round_off...............",round_off)
    #     if provider_name:
    #         # print "provider_name:", provider_name
    #         invoice_data['provider_name'] = ','.join(provider_name)
    #     else:
    #         invoice_data['provider_name'] = ''
    #     invoice_data['taxes'] = taxes
    #     invoice_data['amount_untaxed'] = amount_untaxed
    #     invoice_data['round_off_value'] = round_off
    #     invoice_data['discount'] = discount
    #     invoice_data['net_amount'] = invoice_data['taxes'] + invoice_data['amount_untaxed'] - invoice_data['discount']
    #     invoice_data['outstanding_balance'] = self.partner_id.credit or self.partner_id.debit
    #     print("........................................",self.partner_id.credit)
    #     print("........................................",self.partner_id.debit)
    #     invoice_data['paid_amount'] = self.amount
    #     invoice_data['previous_balance'] = invoice_data['outstanding_balance'] - (bill_amount - invoice_data['paid_amount'])
    #     invoice_data['bill_amount'] = invoice_data['net_amount'] + invoice_data['previous_balance']
    #     print(".........222222.....",invoice_data)
    #     return invoice_data
    @api.multi
    def get_invoice_lines(self):
        print('$$$$$$$$$$$$$$$$$$$$4')
        _logger.info("Inside inherited AccountPayment")
        invoice_data = super(AccountPayment, self).get_invoice_lines()
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz(self._context.get('tz'))
        dateofAdmission = ""
        dateofDischarge = ""
        daysinhosp = ""
        Consultant = ""
        round_off=0
        print("invoice_data===>",invoice_data)
        paid_words = 'Rs ' + convertToWords(int(invoice_data['paid_amount'])) + ' Only'
        if paid_words:
            invoice_data['paid_words'] = paid_words
        if not self.invoice_ids:
            invoice_data['bill_date'] = ''
            invoice_data['bill_confirm_date'] = ''

        for inv in self.invoice_ids:
            round_off+=inv.round_off_value
            sale_order = self.env['sale.order'].search([('name', '=', inv.origin)])
            if (sale_order.dateofAdmission and sale_order.dateofDischarge):
                dateofAdmission = sale_order.dateofAdmission
                utc = datetime.strptime(dateofAdmission, '%Y-%m-%d %H:%M:%S')
                utc = utc.replace(tzinfo=from_zone)
                # Convert time zone
                central = utc.astimezone(to_zone)
                dateofAdmission = datetime.strftime(central, DTF)
                dateofAdmission = datetime.strptime(str(dateofAdmission), "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
                dateofDischarge = sale_order.dateofDischarge
                utc = datetime.strptime(dateofDischarge, '%Y-%m-%d %H:%M:%S')
                utc = utc.replace(tzinfo=from_zone)
                # Convert time zone
                central = utc.astimezone(to_zone)
                dateofDischarge = datetime.strftime(central, DTF)
                dateofDischarge = datetime.strptime(str(dateofDischarge), "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
                daysinhosp = sale_order.daysinhosp
            if inv.date:
                invoice_data['bill_date'] = inv.date
            else:
                invoice_data['bill_date'] = ''
            if inv.date_invoice:
                invoice_data['bill_confirm_date'] = inv.date_invoice
            else:
                invoice_data['bill_confirm_date'] = ''
            if sale_order.provider_name:
                Consultant = sale_order.provider_name
            else:
                Consultant = 'NA'

        if Consultant:
            invoice_data['Consultant'] = Consultant
        else:
            invoice_data['Consultant'] = 'NA'
        if (dateofAdmission and dateofDischarge):
            invoice_data['dateofAdmission'] = dateofAdmission
            invoice_data['dateofDischarge'] = dateofDischarge
            invoice_data['daysinhosp'] = daysinhosp
        else:
            invoice_data['dateofAdmission'] = ''
            invoice_data['dateofDischarge'] = ''
            invoice_data['daysinhosp'] = ''
        invoice_data['round_off_value'] = round_off
        invoice_data['payment_mode'] = self.journal_id.name

        return invoice_data
    

    @api.multi
    def post(self):
        super(AccountPayment, self).post()
        for rec in self:
            for operation in self:
                    receipts = self.env['account.payment'].search([
                        ('id', '=', rec.id),
                    ])

            if len(receipts) > 1:
                #need to have both form and tree view so that can click on the tree to view form
                views = [(self.env.ref('account.payment.tree').id, 'tree'), (self.env.ref('account.payment.form').id, 'form')]
                return{
                    'name': 'Payment Receipts',
                    'view_type': 'tree',
                    'view_mode': 'tree,form',
                    'view_id': False,
                    'res_model': 'account.payment',
                    'views': views,
                    'domain': [('id', 'in', receipts.id)],
                    'type': 'ir.actions.act_window',
                }
            else:
                return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.payment',
                'res_id': receipts.id or False,   
                'type': 'ir.actions.act_window',
                'target': 'popup',  
                }
        

    @api.multi
    def print_payment(self):
        return self.env['report'].get_action(self, 'bahmni_odoo_module.bahmni_report_account_payment_template')

    @api.multi  
    def print_insurance_bill(self): 
        return self.env['report'].get_action(self, 'bahmni_odoo_module.bahmni_insurance_print_report_template')

    @api.multi
    def print_advance(self):
        return self.env['report'].get_action(self, 'bahmni_odoo_module.iplit_advance_print_report_template')



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def print_payment(self):
        print("----")
        return self.env['report'].get_action(self, 'bahmni_odoo_module.bahmni_report_invoice_payment_document')

    @api.multi  
    def get_invoice_lines(self):
        print('#####################3')
        _logger.info("Inside Insurance print")
        _logger.info("Inside inherited AccountPayment")
        print("====invoicee==>>")
        #bill = super(AccountPayment, self).get_invoice_lines()
        #invoice_data = super(AccountPayment, self).get_invoice_lines()
        bill={}
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz(self._context.get('tz'))
        dateofAdmission = ""
        dateofDischarge = ""
        daysinhosp = "" 
        Consultant = "" 
        paid_words = 'Rs ' + convertToWords(int(self.amount_total)) + ' Only'
        #bill_words = 'Rs ' + convertToWords(int(invoice_data['bill_amount'])) + ' Only'
        invoice_lines_lists = []
        invoice_lines = []
        round_off=0.0
        for inv in self:
            print(inv.round_off_value,'invVVVVVVVVVVVVVVVVV')
            round_off += inv.round_off_value
            print('round_off***',round_off)
            sale_order = self.env['sale.order'].search([('name', '=', inv.origin)])
            if (sale_order.dateofAdmission and sale_order.dateofDischarge):
                dateofAdmission = sale_order.dateofAdmission
                utc = datetime.strptime(dateofAdmission, '%Y-%m-%d %H:%M:%S')
                utc = utc.replace(tzinfo=from_zone)
                # Convert time zone
                central = utc.astimezone(to_zone)
                dateofAdmission = datetime.strftime(central, DTF)
                dateofAdmission = datetime.strptime(str(dateofAdmission), "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
                dateofDischarge = sale_order.dateofDischarge
                utc = datetime.strptime(dateofDischarge, '%Y-%m-%d %H:%M:%S')
                utc = utc.replace(tzinfo=from_zone)
                # Convert time zone
                central = utc.astimezone(to_zone)
                dateofDischarge = datetime.strftime(central, DTF)
                dateofDischarge = datetime.strptime(str(dateofDischarge), "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
                daysinhosp = sale_order.daysinhosp
            if sale_order:
                Consultant = sale_order.provider_name
            else:
                Consultant = 'NA'

            kg={}
            for key, group in groupby(inv.invoice_line_ids, lambda r: r.product_id.categ_id.name):
                if not kg.get(key,False):
                    kg.update({key: [g for g in group]})
                else:
                    kg.get(key).extend([g for g in group])
            for k in sorted(kg):
                key=k
                group=kg.get(key)
                total=0
                print("group=============>>",group)
                for invoice_line_item in group:
                    print("product",invoice_line_item.product_id)

                    tax_code,taxes='',0
                    name=invoice_line_item.product_id.name
                    if invoice_line_item.invoice_line_tax_ids:
                        print("invoice_line_item.invoice_line_tax_ids",invoice_line_item.invoice_line_tax_ids)
                        for tax_name in invoice_line_item.invoice_line_tax_ids:
                            print("tax_nameeee",tax_name)
                            print("tax_nameeee",tax_name.name)
                            print("tax_nameeee",tax_name.amount)
                            tax_code+=tax_name.name

                            taxes +=tax_name.amount
                    print("invoice_line_item.invoice_line_tax_ids",invoice_line_item.invoice_line_tax_ids)
                    invoice_lines_lists.append({
                    'product_name': name,
                    'price_unit': invoice_line_item.price_unit,
                    'subtotal': invoice_line_item.price_subtotal,
                    'product_category': invoice_line_item.product_id.categ_id.name,
                    'expiry_date': invoice_line_item.expiry_date if invoice_line_item.expiry_date else None,
                    'quantity': invoice_line_item.quantity,
                    'unit_qty':invoice_line_item.uom_id.name or 1,
                    'is_category': False,
                    'is_subtotal':False,
                    'is_line':True,
                    'taxes':taxes,
                    'tax_code':tax_code,
                    'batch_name':invoice_line_item.lot_id.name or False
                    })
                    total+=invoice_line_item.price_subtotal
                print("invoice_lines_lists......................................",invoice_lines_lists)

            bill['invoice_lines_lists'] = invoice_lines_lists   
            bill['amount_untaxed'] = self.amount_untaxed
            bill['round_off_value'] = round_off
            bill['taxes'] = self.amount_tax 
            bill['discount'] = self.discount
            bill['net_amount'] = self.amount_total
            bill['outstanding_balance'] = self.partner_id.credit or self.partner_id.debit
            bill['paid_amount'] = self.amount_total
            bill['previous_balance'] = bill['outstanding_balance'] 
            bill['bill_amount'] = bill['net_amount']
            
            
            if self.date:
                bill['bill_date'] = self.date
            else:
                bill['bill_date'] = ''
            if self.date_invoice:
                bill['bill_confirm_date'] = self.date_invoice
            else:
                bill['bill_confirm_date'] = ''
            #bill['invoice_lines_lists'] = invoice_lines_lists
            if paid_words:
                bill['paid_words'] = paid_words
            #else:
            #    bill['paid_words']=''
            #if bill_words:
            #    bill['bill_words'] = bill_words
            if Consultant:
                bill['Consultant'] = Consultant
            else:
                bill['Consultant'] = ''
            if (dateofAdmission and dateofDischarge):
                bill['dateofAdmission'] = dateofAdmission
                bill['dateofDischarge'] = dateofDischarge
                bill['daysinhosp'] = daysinhosp
            else:
                bill['dateofAdmission'] = ''
                bill['dateofDischarge'] = ''
                bill['daysinhosp'] = ''
            bill['payment_mode'] = self.journal_id.name
            print("bill==================>>>",bill)
            #ghjk
            return bill
