# -*- coding: utf-8 -*-
from itertools import groupby
from odoo import models, fields, api
from odoo.tools import amount_to_text_en, float_round, float_compare
import math

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def get_invoice_lines(self):
        print('%%%%%%%%%%%%%%%%%%%%%%')
        provider_name = []
        taxes = 0.0
        amount_untaxed = 0.0
        discount = 0.0
        round_off=0.0
        bill_amount = 0.0
        invoice_data = {'taxes': 0.0,
                        'amount_untaxed': 0.0,
                        'discount': 0.0,
                        'net_amount': 0.0,
                        'previous_balance': 0.0,
                        'bill_amount': 0.0,
                        'paid_amount': 0.0,
                        'outstanding_balance': 0.0}
        invoice_lines = []
        amount_in_words = amount_to_text_en.amount_to_text(math.floor(self.amount), lang='en', currency='')
        amt = amount_in_words.replace(' and Zero Cent', '')
        for inv in self.invoice_ids:
            sale_order = self.env['sale.order'].search([('name', '=', inv.origin)])
            invoice_data['place_of_supply']= sale_order.place_of_supply.state_id.name
            if sale_order.provider_name:
                provider_name.append(sale_order.provider_name)
            taxes += inv.amount_tax
            amount_untaxed += inv.amount_untaxed
            round_off+=inv.round_off_value
            discount += inv.discount
            bill_amount += inv.amount_total
            for line in inv.invoice_line_ids:
                print('line=======',line)
                tax_code = ''
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                print('price===',price)
                print(line.invoice_id.currency_id, 'line.invoice_id.currency_id=====')
                print(line.quantity, 'line.quantity=====')
                print(line.product_id, 'line.product_id=====')
                print(line.invoice_id.partner_shipping_id, 'line.invoice_id.partner_shipping_id=====')


                tax = line.invoice_line_tax_ids.compute_all(price,line.invoice_id.currency_id,line.quantity,
                                                                           product=line.product_id,
                                                                           partner=line.invoice_id.partner_shipping_id)
                print(tax, 'taxes=====')



                line.total_with_tax = sum(
                    t.get('amount', 0.0) for t in tax.get('taxes', [])) + line.price_subtotal
                print(line.total_with_tax,'line.total_with_tax=========')
                if line.invoice_line_tax_ids:
                        for tax_name in line.invoice_line_tax_ids:
                            tax_code+=tax_name.name
                invoice_lines.append({'product_name': line.product_id.name,
                                      'expiry_date': line.expiry_date,
                                      'hsn_code': line.product_id.hsncode.hsncode ,
                                      'total_with_tax': line.total_with_tax,
                                      'quantity': line.quantity,
                                      'price_unit': line.price_unit,
                                      'tax_code':tax_code,
                                      'taxes':0,
                                      'discount': line.discount,
                                      'batch_name':line.lot_id and line.lot_id.name or '',
                                      'price_subtotal': line.price_subtotal})
                print(invoice_lines,'invoice_lines============')
        invoice_data['invoice_lines'] = invoice_lines
        if provider_name:
            # print "provider_name:", provider_name
            invoice_data['provider_name'] = ','.join(provider_name)
        else:
            invoice_data['provider_name'] = ''
        invoice_data['taxes'] = taxes
        invoice_data['amount_untaxed'] = amount_untaxed
        invoice_data['round_off_value'] = round_off
        invoice_data['discount'] = discount
        invoice_data['net_amount'] = invoice_data['taxes'] + invoice_data['amount_untaxed'] - invoice_data['discount']
        invoice_data['outstanding_balance'] = self.partner_id.credit or self.partner_id.debit
        print("........................................",self.partner_id.credit)
        print("........................................",self.partner_id.debit)
        invoice_data['paid_amount'] = self.amount
        invoice_data['amt'] = amt
        invoice_data['previous_balance'] = invoice_data['outstanding_balance'] - (bill_amount - invoice_data['paid_amount'])
        invoice_data['bill_amount'] = invoice_data['net_amount'] + invoice_data['previous_balance']
        print('invoice_data===',invoice_data)
        return invoice_data

    @api.multi
    def print_payment(self):
        return self.env['report'].get_action(self, 'bahmni_stock.report_account_payment_template')
