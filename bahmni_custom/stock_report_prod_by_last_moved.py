from odoo.exceptions import UserError
from odoo import fields, models ,tools

class prod_last_moved_report(models.Model):
    _name = "prod_last_moved.report"
    _description = "Products report by last moved"
    _auto = False
    _order = 'last_moved_date desc'
   
    product_id = fields.Many2one('product.product', 'Product', readonly=True, select=True)
    origin = fields.Text('Source', readonly=True)
    location_id = fields.Many2one('stock.location', 'Source Location', readonly=True, select=True)
    location_dest_id = fields.Many2one('stock.location', 'Destination Location', readonly=True, select=True)
    last_moved_date = fields.Date('Last Moved Date', readonly=True)
    

    def init(self):
        tools.drop_view_if_exists(self._cr, 'prod_last_moved_report')
        self.env.cr.execute("""
            create or replace view prod_last_moved_report as (
                SELECT
                  sm.id,
                  sm.name            AS desc,
                  sm.origin,
                  sm.location_id,
                  sm.location_dest_id,
                  sm.product_id,
                  stock_picking_time AS last_moved_date
                FROM stock_move sm
                    JOIN (
                           SELECT
                             max(id) AS id
                           FROM stock_move osm
                           WHERE (product_id, stock_picking_time) IN
                                 (SELECT
                                    sm.product_id,
                                    max(sm.stock_picking_time)
                                  FROM stock_move sm
                                  GROUP BY product_id)
                           GROUP BY product_id) AS csm
                      ON sm.id = csm.id
            )""")

    def unlink(self):
        raise UserError(_('Error!'), _('You cannot delete any record!'))

