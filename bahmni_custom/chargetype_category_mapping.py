# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
import logging
from logging import getLogger
_logger = getLogger(__name__)


class syncjob_chargetype_category_mapping(models.Model):
    _name = 'syncjob.chargetype.category.mapping'
    _description = "Chargetype"

    chargetype_name=fields.Char('Chargetype Name',required='True')
    category_id=fields.Many2one('product.category',required='True')


    # @api.model
    # def create(self,values):

    #     res=self.env['syncjob.chargetype.category.mapping'].search([('category_id', '=', values['category_id'])], limit=1)
    #     if len(res)>0:
    #         self.write(values)
    #         dept = res[0].id
    #     else :
    #         dept = super(syncjob_chargetype_category_mapping,self).create(values).id
    #         #dept = osv.Model.create(self,cr, uid, values, context)
    #     return dept
