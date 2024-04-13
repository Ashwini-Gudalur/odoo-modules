from odoo import fields, models, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
	
    shop_id = fields.Many2one('sale.shop', 'Shop')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    total_with_tax = fields.Float('Total with tax')

    # @api.onchange('invoice_line_tax_ids', 'price_subtotal')
    # def onchange_tax_id(self):
    #     price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
    #     print(price, 'price=====')
    #     taxes = self.invoice_line_tax_ids.compute_all(price, self.invoice_id.currency_id, self.quantity, product=self.product_id,
    #                                     partner=self.invoice_id.partner_shipping_id)
    #     print(taxes, 'taxes=====')
    #
    #     self.total_with_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])) + self.price_subtotal
    #     print(self.total_with_tax, 'total_with_tax=====')
