
from openerp.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError
from odoo import fields, models ,tools


class prodlots_report(models.Model):
    _name = "prodlots.report"
    _description = "Stock report by serial number"
    _auto = False
   
    qty = fields.Float('Quantity', readonly=True)
    reorder_level = fields.Float('Reorder Level', readonly=True)
    location_id = fields.Many2one('stock.location', 'Location', readonly=True, select=True)
    category = fields.Char('Product Type', readonly=True, select=True)
    list_price = fields.Char('Sale Price', readonly=True, select=True)
    value = fields.Char('Value', readonly=True, select=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True, select=True)
    prodlot_id = fields.Many2one('stock.production.lot', 'Serial Number', readonly=True, select=True)
    life_date = fields.Date('Expiry Date', readonly=True)
    unit_id = fields.Many2one('product.uom', 'Units', readonly=True, select=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr,  'prodlots_report')
        self.env.cr.execute("""  create or replace view prodlots_report as (
        select ROW_NUMBER() OVER (ORDER BY prodlot_id) as id , report_without_unit.location_id as location_id,prodlot_id,
          (qty * product_uom.factor) as qty,
          product_category.name as category,
          (case WHEN (sale_price != 0) then sale_price else list_price end ) as list_price,
          (case WHEN (sale_price != 0) then qty*sale_price else qty*list_price end) as value,
          report_without_unit.product_id,
          life_date,
          product_uom.id as unit_id,
          swo.product_min_qty as reorder_level
            from
            (select  location_id, product_id, prodlot_id, sale_price, life_date, sum(qty) as qty
             from (
                    select spl.product_id ,sq.location_id ,spl.id as prodlot_id ,spl.sale_price,spl.life_date ,sum(sq.qty) as qty 
                    from stock_production_lot spl
                    left join stock_quant sq on spl.id = sq.lot_id 
                    left join stock_location sl on sl.id = sq.location_id 
                    where sl.usage = 'internal'
                    group by sq.location_id ,spl.id ,spl.sale_price,spl.life_date 
              
                  ) as report
                  group  by   location_id, product_id, prodlot_id, sale_price,life_date
                  ) as report_without_unit
                  left join product_product on (product_product.id=report_without_unit.product_id)
                  left join product_template on (product_template.id=product_product.product_tmpl_id)
                  left join product_category on (product_category.id=product_template.categ_id)
                  left join product_uom on (product_uom.id=product_template.uom_id)
                  left join stock_warehouse_orderpoint swo on (product_product.id=swo.product_id) and swo.active = true
                 group by report_without_unit.location_id,product_category.name ,report_without_unit.product_id,
                  (case WHEN (sale_price != 0) then qty*sale_price else qty*list_price end),
                    report_without_unit.product_id,
          life_date,
          product_uom.id ,
          swo.product_min_qty,prodlot_id,qty,sale_price,list_price
                  )""")

    # def init(self):
    #     tools.drop_view_if_exists(self._cr,  'prodlots_report')
    #     self.env.cr.execute("""  create or replace view prodlots_report as (
    #     select report_without_unit.id,report_without_unit.location_id as location_id,prodlot_id,
    #       (qty * product_uom.factor) as qty,
    #       product_category.name as category,
    #       (case WHEN (sale_price != 0) then sale_price else list_price end ) as list_price,
    #       (case WHEN (sale_price != 0) then qty*sale_price else qty*list_price end) as value,
    #       report_without_unit.product_id,
    #       life_date,
    #       product_uom.id as unit_id,
    #       swo.product_min_qty as reorder_level
    #         from
    #         (select max(id) as id, location_id, product_id, prodlot_id, sale_price, life_date, sum(qty) as qty
    #          from (
                    # select -max(sm.id) as id, sm.location_id, sm.product_id, sq.lot_id as prodlot_id, spl.sale_price, spl.life_date, -sum(sm.product_qty /uo.factor) as qty
                    # from stock_move as sm
                    # left join stock_quant_move_rel stqm on (stqm.move_id = sm.id)
                    # left join stock_quant sq on (stqm.quant_id = sq.id)
                    # left join stock_production_lot spl on (spl.id = sm.restrict_lot_id)
                    # left join stock_location sl on (sl.id = sm.location_id)
                    # left join product_uom uo on (uo.id=sm.product_uom)
                    # where state in ('done', 'confirmed') and sl.usage= 'internal'
                    # group by sm.location_id, sm.product_id, sm.product_uom, sq.lot_id, spl.life_date,spl.sale_price

    #                 union all

    #                 select max(sm.id) as id, sm.location_dest_id as location_id, sm.product_id, sq.lot_id as prodlot_id, spl.sale_price, spl.life_date, sum(sm.product_qty /uo.factor) as qty
    #                 from stock_move as sm
    #                 left join stock_quant_move_rel stqm on (stqm.move_id = sm.id)
    #                 left join stock_quant sq on (stqm.quant_id = sq.id)
    #                 left join stock_production_lot spl on (spl.id = sm.restrict_lot_id)
    #                 left join stock_location sl on (sl.id = sm.location_dest_id)
    #                 left join product_uom uo on (uo.id=sm.product_uom)
    #                 where sm.state in ('done', 'confirmed') and sl.usage= 'internal'
    #                 group by sm.location_dest_id, sm.product_id, sm.product_uom, sq.lot_id, spl.life_date,spl.sale_price
    #               ) as report
    #               group by location_id, product_id, prodlot_id, sale_price,life_date
    #               ) as report_without_unit
    #               left join product_product on (product_product.id=report_without_unit.product_id)
    #               left join product_template on (product_template.id=product_product.product_tmpl_id)
    #               left join product_category on (product_category.id=product_template.categ_id)
    #               left join product_uom on (product_uom.id=product_template.uom_id)
    #               left join stock_warehouse_orderpoint swo on (product_product.id=swo.product_id) and swo.active = true)""")


    # def init(self):
    #     tools.drop_view_if_exists(self._cr,  'prodlots_report')
    #     self.env.cr.execute("""  create or replace view prodlots_report as (
    #     select report_without_unit.id,prodlot_id,
    #       (qty * product_uom.factor) as qty,
    #       product_category.name as category,
    #       (case WHEN (sale_price != 0) then sale_price else list_price end ) as list_price,
    #       (case WHEN (sale_price != 0) then qty*sale_price else qty*list_price end) as value,
    #       report_without_unit.product_id,
    #       life_date,
    #       product_uom.id as unit_id,
    #       swo.product_min_qty as reorder_level
    #         from
    #         (select max(id) as id,  product_id, prodlot_id, sale_price, life_date, sum(qty) as qty
    #          from (
    #               select max(sm.id) as id,  sm.product_id, sq.lot_id as prodlot_id, spl.sale_price, spl.life_date, -sum(sm.product_qty /uo.factor) as qty
    #                 from stock_move as sm
    #                 left join stock_quant_move_rel stqm on (stqm.move_id = sm.id)
    #                 left join stock_quant sq on (stqm.quant_id = sq.id)
    #                 left join stock_production_lot spl on (spl.id = sm.restrict_lot_id)
    #                 left join stock_location sl on (sl.id = sm.location_id)
    #                 left join product_uom uo on (uo.id=sm.product_uom)
    #                 where state in ('done', 'confirmed')  and sl.usage = 'internal'
    #                 group by  sm.product_id, sm.product_uom, sq.lot_id, spl.life_date,spl.sale_price

    #                 union all

    #                 select max(sm.id) as id,  sm.product_id, sq.lot_id as prodlot_id, spl.sale_price, spl.life_date, sum(sm.product_qty /uo.factor) as qty
    #                 from stock_move as sm
    #                 left join stock_quant_move_rel stqm on (stqm.move_id = sm.id)
    #                 left join stock_quant sq on (stqm.quant_id = sq.id)
    #                 left join stock_production_lot spl on (spl.id = sm.restrict_lot_id)
    #                 left join stock_location sl on (sl.id = sm.location_dest_id)
    #                 left join product_uom uo on (uo.id=sm.product_uom)
    #                 where sm.state in ('done', 'confirmed') and sl.usage = 'internal'
    #                 group by sm.location_dest_id, sm.product_id, sm.product_uom,sq.lot_id, spl.life_date,spl.sale_price
    #               ) as report
    #               group by  product_id, prodlot_id, sale_price,life_date
    #               ) as report_without_unit
    #               left join product_product on (product_product.id=report_without_unit.product_id)
    #               left join product_template on (product_template.id=product_product.product_tmpl_id)
    #               left join product_category on (product_category.id=product_template.categ_id)
    #               left join product_uom on (product_uom.id=product_template.uom_id)
    #               left join stock_warehouse_orderpoint swo on (product_product.id=swo.product_id) and swo.active = true)""")
    def unlink(self):
        raise UserError(_('Error!'), _('You cannot delete any record!'))



