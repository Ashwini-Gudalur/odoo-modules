from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
from logging import getLogger

_logger = getLogger(__name__)


class claim_type(models.Model):
    _name = 'claim.type'
    _description = "Type of program"


    # claim_type=fields.Selection([('1', 'Sickle Cell'), ('2', 'Bed Grant'),('3', 'CMCHIS')], 'Claim Type')
    # erp_patient_id=fields.Many2one('res.partner','ERP Patient Id',required=True)
    name  =  fields.Char('Name',required=True )
    # @api.model
    # def create(self, vals):

    #     res=self.env('claim.type').search([('erp_patient_id', '=', vals['erp_patient_id'])], limit=1)
    #     if len(res)>0:
    #         # super(osv.osv, self).write(cr, uid, ids, vals, context=context)
    #         # record = self.browse(cr,uid,res)
    #         # claim_type.write({'claim_type': values['claim_type']})
    #         #super(claim_type, self).write(vals)
    #         #self.write(vals)
    #         erp_patient = res[0]
    #         # _logger('claim_type------create----------%s',erp_patient)
    #     else :
    #         erp_patient = super(claim_type,self).create(vals)
    #     return erp_patient

