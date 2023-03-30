# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RoundOffSetting(models.TransientModel):
    _inherit = 'account.config.settings'

    round_off = fields.Boolean(string='Allow rounding of invoice amount', help="Allow rounding of invoice amount")
    round_off_account = fields.Many2one('account.account', string='Round Off Account')

    @api.multi
    def set_round_off(self):
        ir_values_obj = self.env['ir.values']
        ir_values_obj.sudo().set_default('account.config.settings', "round_off", self.round_off)
        ir_values_obj.sudo().set_default('account.config.settings', "round_off_account", self.round_off_account.id)


