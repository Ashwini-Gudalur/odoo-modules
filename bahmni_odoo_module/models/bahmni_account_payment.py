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
     
    @api.multi
    def get_invoice_lines(self):
        _logger.info("Inside inherited AccountPayment")
        invoice_data = super(AccountPayment, self).get_invoice_lines()
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz(self._context.get('tz'))
        dateofAdmission = ""
        dateofDischarge = ""
        daysinhosp = ""
        Consultant = ""
        print("invoice_data===>",invoice_data)
        paid_words = 'Rs ' + convertToWords(int(invoice_data['paid_amount'])) + ' Only'
        if paid_words:
            invoice_data['paid_words'] = paid_words
        if not self.invoice_ids:
            invoice_data['bill_date'] = ''
            invoice_data['bill_confirm_date'] = ''

        for inv in self.invoice_ids:
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
        for inv in self:
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
            bill['taxes'] = self.amount_tax 
            bill['discount'] = self.discount
            bill['net_amount'] = self.amount_total
            bill['outstanding_balance'] = self.partner_id.credit or self.partner_id.debit
            bill['paid_amount'] = self.amount_total
            bill['previous_balance'] = bill['outstanding_balance'] + bill['net_amount']
            bill['bill_amount'] = bill['net_amount'] + bill['previous_balance']
            
            
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
