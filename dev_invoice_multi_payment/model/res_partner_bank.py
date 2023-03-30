# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://devintellecs.com>).
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

    
class res_partner_bank(models.Model):
    _inherit = 'res.partner.bank'
    
    payment_type = fields.Many2one('dev.payment.type',string='Payment Type')
    acc_number = fields.Char('Account Number', required=False)
            
    
             
