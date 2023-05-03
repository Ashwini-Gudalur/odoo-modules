# -*- coding: utf-8 -*-
from itertools import groupby
from odoo import models, fields, api
MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

class AccountAbstractPayment(models.AbstractModel):
    _inherit = 'account.abstract.payment'

# commented as per Ajeenckya's suggestion, as keeping bank journals in selection, will fulfill the generic way of using payment
#     journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True,
#                                  domain=[('type', '=', 'cash')])


class AccountPayment(models.Model):
    _inherit = 'account.payment'

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

    @api.onchange('partner_id', 'amount')
    def _calculate_balances(self):
        for rec in self:
            balance = rec._total_receivable()
            if(rec.state != 'posted'):
                rec.balance_before_pay = balance
                rec.total_balance = balance - rec.amount
            else:
                rec.balance_before_pay = balance
                rec.total_balance = balance 

    # @api.onchange('partner_id', 'amount')
    # def _calculate_balances(self):
    #     for rec in self:
    #         if(rec.state != 'posted'):
    #             partner = rec.partner_id
    #             balance = partner.credit or partner.debit
    #             rec.balance_before_pay = balance
    #             rec.total_balance = balance - rec.amount

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if not self.invoice_ids:
            # Set default partner type for the payment type
            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
            elif self.payment_type == 'outbound':
                self.partner_type = 'supplier'
            else:
                self.partner_type = False
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        res['domain']['journal_id'] = self.payment_type == 'inbound' and [('at_least_one_inbound', '=', True)] or self.payment_type == 'outbound' and [('at_least_one_outbound', '=', True)] or []
        #res['domain']['journal_id'].append(('type', '=', 'cash'))
        return res

    balance_before_pay = fields.Float(compute=_calculate_balances,
                                      string="Balance before pay")
    total_balance = fields.Float(compute=_calculate_balances,
                                 string="Total Balance")
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    bill_amount = fields.Float(string="Bill Amount")

    def write(self, vals):
        res = super(AccountPayment, self).write(vals)
        if not self.invoice_ids and self.invoice_id and self.payment_type == 'outbound' and self.state == 'posted':
            self.invoice_ids = [(6, 0, self.invoice_id.ids)]
        return res

