from odoo import fields, models

class syncjob_department_category_mapping(models.Model):
    _name = 'syncjob.department.category.mapping'
    _description = "Department"


   
    department_name = fields.Char('Department',required=True)
    category_id =fields.Many2one('product.category','Category Id',required=True,unique=True)
    
    # @api.model
    # def create(self, values, context=None):

    #     res=self.env['syncjob.department.category.mapping'].search([('category_id', '=', values['category_id'])], limit=1)
    #     if len(res)>0:
    #         super(syncjob_department_category_mapping, self).write(res, values, context)
    #         dept = res[0];
    #     else :
    #         dept = osv.Model.create(self,values, context)
    #     return dept


