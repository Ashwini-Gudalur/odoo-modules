# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://devintellecs.com>).
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

    
class account_payment(models.Model):
    _inherit = 'account.payment'
    
    line_ids = fields.One2many('advance.payment.line','account_payment_id')
    
    
    def _get_counterpart_move_line_vals(self, invoice=False):
        res = super(account_payment,self)._get_counterpart_move_line_vals(invoice)
        if self.payment_type == 'outbound' and self.partner_type == 'supplier':
            if invoice:
                name = ''
                for inv in invoice:
                    if inv.reference:
                        if name :
                            name = name + ','+inv.reference
                        else:
                            name = inv.reference
                res.update({
                    'name':name,
                })
        return res
    
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        acc_invoice = []
        account_inv_obj = self.env['account.invoice']
        invoice_ids=[]
        if self.partner_type == 'customer':
            invoice_ids = account_inv_obj.search([('partner_id', 'in', [self.partner_id.id]),('state', '=','open'),('type','in',['out_invoice','out_refund'])])
        else:
            invoice_ids = account_inv_obj.search([('partner_id', 'in', [self.partner_id.id]),('state', '=','open'),('type','in',['in_invoice','in_refund'])])
        curr_pool=self.env['res.currency']
        for vals in invoice_ids: 
            ref = ''
            if self.partner_type == 'customer':
                ref = vals.name
            else:
                ref = vals.reference
                
            original_amount = vals.amount_total
            balance_amount = vals.residual
            allocation = vals.residual
            if vals.currency_id.id != self.currency_id.id:
            	currency_id = self.currency_id.with_context(date=self.payment_date)
                original_amount = curr_pool._compute(vals.currency_id, currency_id, original_amount, round=True)
                balance_amount = curr_pool._compute(vals.currency_id, currency_id, balance_amount, round=True)
                allocation = curr_pool._compute(vals.currency_id, currency_id, allocation, round=True)
            
            acc_invoice.append({'invoice_id':vals.id,'account_id':vals.account_id.id,
            'date':vals.date_invoice,'due_date':vals.date_due,
            'original_amount':original_amount,'balance_amount':balance_amount,
            'allocation':allocation,'full_reconclle':True,'reference':ref,'currency_id':self.currency_id.id})
        self.line_ids = acc_invoice
        
    
    @api.onchange('currency_id')
    def onchange_currency(self):
    	curr_pool=self.env['res.currency']
    	if self.currency_id and self.line_ids:
    		for line in self.line_ids:
    			if line.currency_id.id != self.currency_id.id:
    				currency_id = self.currency_id.with_context(date=self.payment_date)
    				line.original_amount = curr_pool._compute(line.currency_id, currency_id, line.original_amount, round=True)
    				line.balance_amount = curr_pool._compute(line.currency_id, currency_id, line.balance_amount, round=True)
    				line.allocation = curr_pool._compute(line.currency_id, currency_id, line.allocation, round=True)
    				line.currency_id = self.currency_id and self.currency_id.id or False
        
    @api.model
    def create(self,vals):
        if vals.get('line_ids'):
            inv_ids = []
            for line in vals.get('line_ids'):
                inv_ids.append(line[2].get('invoice_id'))
                
            vals.update({
            'invoice_ids':[(6,0,inv_ids)]
            })
        payment_ids=super(account_payment,self).create(vals)
        return payment_ids
    
    @api.multi
    def post(self):     
        if self.line_ids:
            amt=0.0
            for line in self.line_ids:
                amt += line.allocation
            if self.amount < amt:
                raise ValidationError(("Amount is must be greater or equal '%s'") %(amt))
            if self.amount > amt:
                for line in self.line_ids:
                    line.allocation = line.allocation + (self.amount - amt)
                    break
        return  super(account_payment,self).post()
    
    @api.multi
    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment
            references invoice(s) they are reconciled.
            Return the journal entry.
        """
        # If group data
        if self.invoice_ids and self.line_ids:
            aml_obj = self.env['account.move.line'].\
                with_context(check_move_validity=False)
            invoice_currency = False
            if self.invoice_ids and\
                    all([x.currency_id == self.invoice_ids[0].currency_id
                         for x in self.invoice_ids]):
                # If all the invoices selected share the same currency,
                # record the paiement in that currency too
                invoice_currency = self.invoice_ids[0].currency_id
            move = self.env['account.move'].create(self._get_move_vals())
            p_id = str(self.partner_id.id)
            for inv in self.invoice_ids:
                amt = 0
                if self.partner_type == 'customer':
                    for line in self.line_ids:
                        if line.invoice_id.id == inv.id:
                        	if inv.type == 'out_invoice':
                        		amt = -(line.allocation)
                        	else:
                        		amt = line.allocation
                else:
                    for line in self.line_ids:
                        if line.invoice_id.id == inv.id:
                        	if inv.type == 'in_invoice':
                        		amt = line.allocation
                        	else:
                        		amt = -(line.allocation)

                debit, credit, amount_currency, currency_id =\
                    aml_obj.with_context(date=self.payment_date).\
                    compute_amount_fields(amt, self.currency_id,
                                          self.company_id.currency_id,
                                          invoice_currency)
                # Write line corresponding to invoice payment
                counterpart_aml_dict =\
                    self._get_shared_move_line_vals(debit,
                                                    credit, amount_currency,
                                                    move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(inv))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                # Reconcile with the invoices and write off
                if self.partner_type == 'customer':
                    handling = 'open'  # noqa
                    for line in self.line_ids:
                        if line.invoice_id.id == inv.id:
                            payment_difference = line.balance_amount - line.allocation  # noqa
                    writeoff_account_id = self.journal_id and self.journal_id.id or False  # noqa
                    if handling == 'reconcile' and\
                            payment_difference:
                        writeoff_line =\
                            self._get_shared_move_line_vals(0, 0, 0, move.id,
                                                            False)
                        debit_wo, credit_wo, amount_currency_wo, currency_id =\
                            aml_obj.with_context(date=self.payment_date).\
                            compute_amount_fields(
                                payment_difference,
                                self.currency_id,
                                self.company_id.currency_id,
                                invoice_currency)
                        writeoff_line['name'] = _('Counterpart')
                        writeoff_line['account_id'] = writeoff_account_id
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = credit_wo
                        writeoff_line['amount_currency'] = amount_currency_wo
                        writeoff_line['currency_id'] = currency_id
                        writeoff_line = aml_obj.create(writeoff_line)
                        if counterpart_aml['debit']:
                            counterpart_aml['debit'] += credit_wo - debit_wo
                        if counterpart_aml['credit']:
                            counterpart_aml['credit'] += debit_wo - credit_wo
                        counterpart_aml['amount_currency'] -=\
                            amount_currency_wo
                inv.register_payment(counterpart_aml)
                # Write counterpart lines
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                liquidity_aml_dict =\
                    self._get_shared_move_line_vals(credit, debit,
                                                    -amount_currency, move.id,
                                                    False)
                liquidity_aml_dict.update(
                    self._get_liquidity_move_line_vals(-amount))
                aml_obj.create(liquidity_aml_dict)
            move.post()
            return move

        return super(account_payment, self)._create_payment_entry(amount)
    
    
        
