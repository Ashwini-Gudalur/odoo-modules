from odoo import models, fields, api
from datetime import datetime, timedelta

class AccountInvoiceInherit(models.Model):
    _inherit = 'account.invoice'
    care_setting = fields.Selection([('ipd', 'IPD'),
                                     ('opd', 'OPD')], string="Care Setting")
    doctor_name = fields.Char()

    def get_payment_datetime(self):
        account_payment = self.env['account.payment'].search([('id', '=', self.payment_ids.id)])
        if not account_payment:
            utc_date = datetime.strptime(self.create_date, '%Y-%m-%d %H:%M:%S')
            ist_time = utc_date + timedelta(hours=5, minutes=30)
            return ist_time
        else:
            utc_date = datetime.strptime(account_payment.create_date, '%Y-%m-%d %H:%M:%S')
            ist_time = utc_date + timedelta(hours=5, minutes=30)
            return ist_time
