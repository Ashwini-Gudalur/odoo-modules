from odoo import models, fields, api

class saleorderWizard(models.TransientModel):
    _name = 'select.customers.wizard'
    _description = "Selection Customer"

    partner_ids = fields.Many2one('res.partner',"Partner")

    def add_partner(self):
            if self.partner_ids:
                action_context = ({'partner_ids': self.partner_ids.ids})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'manual_reconciliation_view',
                    'context': action_context,
                    'target': 'new',
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'manual_reconciliation_view',
                    'target': 'new',
                }
