# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')

    def _get_notes(self):
        for purchase in self:
            if purchase.notes:
                purchase.note = purchase.notes[0:15] + "..."

    note = fields.Text(string='Notes', compute='_get_notes')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    code_product = fields.Char('Product Code')

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        # Function override to get unit price while qty is in minus.
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)
        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            # When products qty is in minus, passing cost to unit price.
            if self.product_qty < 0:
                self.price_unit = self.product_id.standard_price
            # Closed based condition to achive above one.a
            # if self.product_id.seller_ids.filtered(lambda s: s.name.id == self.partner_id.id):
            #     self.price_unit = 0.0
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
        self.price_unit = price_unit

        if seller:
            # When products code is set on vendor so by default set on that.
            self.code_product = seller.product_code


    @api.multi
    def _prepare_stock_moves(self, picking):
        # FUnction override to pass decreased qty to move.
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            # Always call '_compute_quantity' to round the diff_quantity. Indeed, the PO quantity
            # is not rounded automatically following the UoM.
            if get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = self.product_uom._compute_quantity(diff_quantity, self.product_uom, rounding_method='HALF-UP')
            res.append(template)
        # append decreased qty in moves.
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) < 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            # Always call '_compute_quantity' to round the diff_quantity. Indeed, the PO quantity
            # is not rounded automatically following the UoM.
            if get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = self.product_uom._compute_quantity(diff_quantity, self.product_uom, rounding_method='HALF-UP')
            res.append(template)
        return res

    @api.multi
    def write(self, values):
        """Messsage post when qty change."""
        if 'product_qty' in values:
            for line in self:
                if line.order_id.state != 'purchase':
                    line.order_id.message_post_with_view('purchase.track_po_line_template',
                                                         values={'line': line, 'product_qty': values['product_qty']},
                                                         subtype_id=self.env.ref('mail.mt_note').id)
        if 'price_unit' in values:
            for line in self:
                line._update_line_quantity(values)
        return super(PurchaseOrderLine, self).write(values)

    def _update_line_quantity(self, values):
        """Fucntion call to add message in chatter when qty change."""
        purchase_order = self.mapped('order_id')
        for purchase in purchase_order:
            po_lines = self.filtered(lambda x: x.order_id == purchase)
            msg = "<b>Unit Price has been updated.</b><ul>"
            for line in po_lines:
                msg += "<li> %s:" % (line.product_id.display_name,)
                msg += "<br/>" + _("Unit Price") + ": %s -> %s <br/>" % (
                    line.price_unit, float(values['price_unit']),)
            msg += "</ul>"
            purchase_order.message_post(body=msg)


    def _suggest_quantity(self):
        '''
        Suggest a minimal quantity based on the seller
        '''
        # Function override to set product_qty is 0 .
        if not self.product_id:
            return
        seller_min_qty = self.product_id.seller_ids\
            .filtered(lambda r: r.name == self.order_id.partner_id and (not r.product_id or r.product_id == self.product_id))\
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty:
            self.product_qty = seller_min_qty[0].min_qty or 0.0
            self.product_uom = seller_min_qty[0].product_uom
        else:
            self.product_qty = 0.0
