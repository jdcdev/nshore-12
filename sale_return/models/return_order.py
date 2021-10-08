from datetime import date

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class ReturnOrder(models.Model):
    """Class Return Order."""

    _name = 'return.order'
    _description = 'Return Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Defined fields
    name = fields.Char(
        string="Name", required=1,
        default=lambda self: _('New'), track_visibility='always')
    line_ids = fields.One2many("return.order.line", "return_id", copy=True)
    sale_person_id = fields.Many2one(
        "res.users", string="SalesPerson", required=True,
        default=lambda self: self.env.user and self.env.user.id or False,
        track_visibility='always')
    partner_id = fields.Many2one(
        "res.partner", string="Customer", track_visibility='always')
    date = fields.Date(
        string="Date", required=True,
        default=lambda self: date.today(), track_visibility='always')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancelled'),
        ('done', 'Returned'),
        ('returned_cancel', 'Cancelled'),
    ], default='draft',
        required=True, track_visibility='always')
    credit_invoice_id = fields.Many2one(
        "account.invoice", string="Credit Invoice", track_visibility='always')
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount', currency_field='currency_id', store=False,
        readonly=True, compute='_amount_all', track_sequence=5,
        track_visibility='always')
    amount_tax = fields.Monetary(
        string='Taxes', store=True, readonly=True, compute='_amount_all',
        track_visibility='always')
    amount_total = fields.Monetary(
        string='Total', store=True, readonly=True, compute='_amount_all',
        track_visibility='always')
    price_tax = fields.Float(
        compute='_compute_amount', string='Total Tax',
        readonly=True, store=True)
    currency_id = fields.Many2one('res.currency')
    stock_move_ids = fields.One2many('stock.picking', 'return_order_id')
    account_invoice_ids = fields.One2many('account.invoice', 'return_order_id')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist',
        readonly=True, states={'draft': [('readonly', False)]})
    type_partner = fields.Selection([
        ('supplier', 'Vendor'), ('customer', 'Customer')], default='customer')
    supplier_id = fields.Many2one(
        'res.partner', string="Vendor",
        domain=[('supplier', '=', True)])
    sale_ids = fields.Many2many('sale.order', string="Sales Order")
    purchase_ids = fields.Many2many('purchase.order', string="Purchase Order")
    note = fields.Text('Note')
    notes = fields.Text('Notes', compute='_get_notes')

    @api.onchange('partner_id')
    def onchange_partner(self):
        """Onchange call for customer pricelist."""
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and
                            self.partner_id.property_product_pricelist.id or False,
        }
        self.update(values)

    def _get_notes(self):
        for ro in self:
            ro.notes = ro.note[0:10] + "..." if ro.note else ''

    @api.depends('line_ids.value_before_tax', 'line_ids.price_tax')
    def _amount_all(self):
        for order in self:
            for line in order.line_ids:
                order.amount_untaxed += line.value_before_tax
                order.amount_tax += line.price_tax
                order.amount_total = order.amount_untaxed + order.amount_tax

    @api.multi
    def show_delivery(self):
        """Function call for showing picking."""
        return {
            'name': ('Delivery'),
            'domain': [('return_order_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window'}

    @api.multi
    def show_invoice(self):
        """Function call for showing picking."""
        return {
            'name': ('Credit Note'),
            'domain': [('return_order_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window'}

    @api.model
    def default_get(self, fields):
        """Default get called."""
        rec = super(ReturnOrder, self).default_get(fields)
        active_id = self._context.get('active_id')
        if active_id:
            active_model = self._context.get('active_model')
            if active_model == 'sale.order':
                sale_order = self.env[active_model].browse(active_id)
                rec['partner_id'] = sale_order.partner_id.id
                self.env[
                    'ir.config_parameter'].sudo().set_param(
                    'sale.order.id', active_id)
        else:
            self.env['ir.config_parameter'].sudo().set_param(
                'sale.order.id', '')
        return rec

    @api.multi
    def action_cancel(self):
        """Method to cancel return order."""
        if self.state == 'confirm':
            self.write({'state': 'cancel'})

    @api.multi
    def action_set_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_confirm(self):
        self.write({'state': 'confirm'})

    @api.multi
    def process_return(self):
        """Main method to process return according the return option."""

        self.check_orderline()
        line_ids = self.env['return.order.line'].sudo().search([
            ('return_id', '=', self.id)
        ])
        if line_ids:
            if self.type_partner == 'customer':
                self.process_refund_return_customer(lines=line_ids)
            else:
                self.process_refund_return_vendor(lines=line_ids)

    def process_refund_return_vendor(self, lines):
        """Function call refund from vendor."""
        # Picking type and Location for without PO return line.
        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing')], limit=1)
        location = self.env['stock.location'].search(
            [('usage', '=', 'supplier')], limit=1)
        # Create return picking to vendor.
        picking_return = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type_id.id or False,
            'partner_id': self.supplier_id.id,
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id': location.id,
            'return_order_id': self.id})
        # Create refund note to vendor
        refund_vals = {
            'type': 'in_refund',
            'partner_id': self.supplier_id.id,
            'return_order_id': self.id}
        refund = self.env['account.invoice'].create(refund_vals)
        for return_line in lines.filtered(lambda line: line.product_id):
            # When Purchase order selected in return line
            if return_line.purchase_order_id:
                # Get Vendor Bill Details
                invoice_ids = return_line.purchase_order_id.invoice_ids.filtered(
                    lambda m: m.state not in ['draft', 'cancelled'])
                # Raised warning when seleted PO don't have vendor Bill.
                if not invoice_ids:
                    raise ValidationError(_('Please Create Bill or Check state of Bill for Purchase Order %s.' % return_line.purchase_order_id.name))
                # Invoice Line
                if invoice_ids:
                    self.env['account.invoice.line'].create({
                        'name': return_line.product_id.name or '',
                        'product_id': return_line.product_id.id or False,
                        'account_id':
                            return_line.product_id.property_account_income_id.id or
                            return_line.product_id.categ_id.property_account_income_categ_id.id or False,
                        'quantity': return_line.qty or 0.0,
                        'uom_id':
                            return_line.product_id.product_tmpl_id.uom_id.id or
                            False,
                        'price_unit': return_line.unit_price or 0.0,
                        'invoice_line_tax_ids': [
                                                    (6, 0, return_line.tax_id.ids)] or False,
                        'invoice_id': refund and refund.id or False})
                # Get picking type and Picking from selected Purchase order
                picking_type_id_po = self.env['stock.picking.type'].search([
                    ('code', '=', 'incoming')], limit=1)
                picking_id = self.env['stock.picking'].search(
                    [('group_id', '=', return_line.purchase_order_id.group_id.id),
                     ('product_id', '=', return_line.product_id.id),
                     ('picking_type_id', '=', picking_type_id_po.id),
                     ('state', '=', 'done')], limit=1)
                # Raise warning when selected PO don't have receipt
                if not picking_id:
                    raise ValidationError(
                        """Please make Receipt for this seletced Purchase order first.""")
                # Create return picking
                if picking_id:
                    self.env['stock.move'].sudo().create({
                        'name': return_line.product_id.name,
                        'product_id': return_line.product_id.id,
                        'product_uom':
                            return_line.product_id.product_tmpl_id.uom_id.id,
                        'product_uom_qty': return_line.qty,
                        'location_id':
                            picking_type_id_po.default_location_dest_id.id,
                        'location_dest_id': location.id,
                        'partner_id': self.supplier_id.id,
                        'picking_id': picking_return.id,
                        'picking_type_id': picking_type_id_po.id,
                        'quantity_done': return_line.qty})
                    return_line.sudo().write({'state': 'done'})
                qty_returned = 0.0
                # Update purchase order line with return reference.
                for line in return_line.purchase_order_id.order_line.filtered(
                        lambda l: l.product_id.id == return_line.product_id.id):
                    self.purchase_ids = return_line.purchase_order_id.ids
                    qty_returned = line.return_qty + return_line.qty
                    line.write({'return_qty': qty_returned})
                    if line.product_uom_qty == line.return_qty:
                        line.write({'return_order_id': self.id, 'all_return': True})
                if all(po_lines.all_return for po_lines in return_line.mapped(
                        'purchase_order_id').order_line):
                    return_line.purchase_order_id.write({'state': 'return'})
            # Append stock move and invoice line in created return and credit
            # note without PO
            if not return_line.purchase_order_id:
                # Invoice Line for refund
                self.env['account.invoice.line'].create({
                    'name': return_line.product_id.name or '',
                    'product_id': return_line.product_id.id or False,
                    'account_id':
                        return_line.product_id.property_account_income_id.id or
                        return_line.product_id.categ_id.property_account_income_categ_id.id or False,
                    'quantity': return_line.qty or 0.0,
                    'uom_id':
                        return_line.product_id.product_tmpl_id.uom_id.id or False,
                    'price_unit': return_line.unit_price or 0.0,
                    'invoice_line_tax_ids': [
                                                (6, 0, return_line.tax_id.ids)] or False,
                    'invoice_id': refund and refund.id or False})
                # Stock Move for return
                self.env['stock.move'].sudo().create({
                    'name': return_line.product_id.name,
                    'product_id': return_line.product_id.id,
                    'product_uom':
                        return_line.product_id.product_tmpl_id.uom_id.id,
                    'product_uom_qty': return_line.qty,
                    'location_id': picking_type_id.default_location_src_id.id,
                    'location_dest_id': location.id,
                    'partner_id': self.supplier_id.id,
                    'picking_id': picking_return.id,
                    'picking_type_id': picking_type_id.id,
                    'quantity_done': return_line.qty})
                return_line.sudo().write({'state': 'done'})
        # Validate and done  created return
        if picking_return:
            picking_return.sudo().write(
                {'return_order_id': self.id})
            picking_return.sudo().action_confirm()
            picking_return.sudo().action_assign()
            picking_return.sudo().button_validate()
        # Validate Bill and update Taxes vals.
        if refund:
            refund.sudo().compute_taxes()
            refund.sudo().action_invoice_open()
            refund.sudo().write({'return_order_id': self.id})
        self.sudo().write({'state': 'done'})

    def process_refund_return_customer(self, lines=None):
        """Function call to refund customer."""
        # Picking and location information
        picking_type_id = self.env['stock.picking.type'].sudo().search([
            ('code', '=', 'incoming')], limit=1)
        location = self.env['stock.location'].search(
            [('usage', '=', 'customer')], limit=1)
        # Create return picking
        picking_return = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type_id.id or False,
            'partner_id': self.partner_id.id,
            'location_id': location.id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'return_order_id': self.id})
        # Create Credit note
        credit_note = self.env['account.invoice'].create({
            'type': 'out_refund',
            'partner_id': self.partner_id.id,
            'return_order_id': self.id})
        # Loop for return order line
        for return_line in lines.filtered(lambda line: line.product_id):
            # When Sales order selected in return line
            if return_line.sale_order_id:
                # Get Invoice Details
                invoice_ids = return_line.sale_order_id.invoice_ids.filtered(
                    lambda m: m.state not in ['draft', 'cancelled'])
                if not invoice_ids:
                    raise ValidationError(_('Please Create Invoice or Check state of Invoice for Sales Order %s.' % return_line.sale_order_id.name))
                if invoice_ids:
                    self.env['account.invoice.line'].create({
                        'name': return_line.product_id.name or '',
                        'product_id': return_line.product_id.id or False,
                        'account_id': return_line.product_id.property_account_income_id.id or
                                      return_line.product_id.categ_id.property_account_income_categ_id.id or False,
                        'quantity': return_line.qty or 0.0,
                        'uom_id': return_line.product_id.product_tmpl_id.uom_id.id or False,
                        'price_unit': return_line.unit_price or 0.0,
                        'invoice_line_tax_ids': [
                                                    (6, 0, return_line.tax_id.ids)] or False,
                        'invoice_id': credit_note and credit_note.id or False,
                        'display_type': return_line.display_type})
                # Get Picking type and create merge picking for return
                picking_type_id_so = self.env[
                    'stock.picking.type'].sudo().search([
                    ('code', '=', 'outgoing'),
                    ('warehouse_id', '=', return_line.sale_order_id.warehouse_id.id)])
                picking_id = self.env['stock.picking'].sudo().search(
                    [('group_id', '=', return_line.sale_order_id.procurement_group_id.id),
                     ('product_id', '=', return_line.product_id.id),
                     ('picking_type_id', '=', picking_type_id_so.id),
                     ('state', '=', 'done')], limit=1)
                # Raised waarning when no delivery order for selected SO
                if not picking_id and not return_line.display_type:
                    raise ValidationError(
                        """Please make delivery for this seletced sales order first.""")
                # Create return moves
                if picking_id:
                    self.env['stock.move'].create({
                        'name': return_line.product_id.name,
                        'product_id': return_line.product_id.id,
                        'product_uom': return_line.product_id.product_tmpl_id.uom_id.id,
                        'product_uom_qty': return_line.qty,
                        'location_id': picking_type_id_so.default_location_dest_id.id,
                        'location_dest_id': picking_type_id_so.default_location_src_id.id,
                        'partner_id': self.partner_id.id,
                        'picking_id': picking_return.id,
                        'picking_type_id': picking_type_id_so.id,
                        'quantity_done': return_line.qty})
                # Update sales order line with return reference.
                qty_returned = 0.0
                for line in return_line.sale_order_id.order_line.filtered(
                        lambda l: l.product_id.id == return_line.product_id.id):
                    qty_returned = line.return_qty + return_line.qty
                    line.write({'return_qty': qty_returned})
                    self.sale_ids = return_line.sale_order_id.ids
                    if line.product_uom_qty == line.return_qty:
                        line.write({'return_order_id': self.id, 'all_return': True})
                if all(so_lines.all_return for so_lines in return_line.mapped(
                        'sale_order_id').order_line):
                    return_line.sale_order_id.write({'state': 'return'})
            # When no sales order in return line.
            if not return_line.sale_order_id:
                # Credit Note
                self.env['account.invoice.line'].create({
                    'name': return_line.product_id.name or '',
                    'product_id': return_line.product_id.id or False,
                    'account_id': return_line.product_id.property_account_income_id.id or
                                  return_line.product_id.categ_id.property_account_income_categ_id.id or False,
                    'quantity': return_line.qty or 0.0,
                    'uom_id': return_line.product_id.product_tmpl_id.uom_id.id or False,
                    'price_unit': return_line.unit_price or 0.0,
                    'invoice_line_tax_ids': [(6, 0, return_line.tax_id.ids)] or False,
                    'invoice_id': credit_note and credit_note.id or False,
                    'display_type': return_line.display_type, }),
                # Moves
                self.env['stock.move'].create({
                    'name': return_line.product_id.name,
                    'product_id': return_line.product_id.id,
                    'product_uom': return_line.product_id.product_tmpl_id.uom_id.id,
                    'product_uom_qty': return_line.qty,
                    'location_id': location.id,
                    'location_dest_id': picking_type_id.default_location_dest_id.id,
                    'partner_id': self.partner_id.id,
                    'picking_id': picking_return.id,
                    'picking_type_id': picking_type_id.id,
                    'quantity_done': return_line.qty})
            return_line.sudo().write({'state': 'done'})
        # Validate and write in created picking
        if picking_return:
            picking_return.sudo().write({'return_order_id': self.id})
            picking_return.sudo().action_confirm()
            picking_return.sudo().action_assign()
            picking_return.sudo().button_validate()
        # Validate and write in created credit note.
        if credit_note:
            credit_note.sudo().compute_taxes()
            credit_note.sudo().action_invoice_open()
            credit_note.sudo().write({'return_order_id': self.id})
        self.sudo().write({'state': 'done'})

    def check_orderline(self):
        """Method to check if there is orderline or not."""
        if not self.line_ids.filtered(lambda return_line: return_line.product_id):
            raise ValidationError("""Can not process return as there is no order line
                associated with this record!""")
        for line in self.line_ids.filtered(lambda return_line: return_line.product_id):
            if line.qty == 0:
                raise ValidationError("""Can not process return as there is no return qty in line.
                    Please put return quantity in line!""")

    def check_delivery_status(self):
        """Method to check if there is delivery done or not."""
        line_record = self.line_ids
        for record in line_record:
            for rec in record.sale_order_id.order_line:
                if rec.qty_delivered < rec.product_uom_qty:
                    raise ValidationError(
                        """Return can not be processed because there is an
                        incomplete or undelivered of this Sale Order""")

    @api.model
    def create(self, vals):
        """Overriding the create method to add the sequence."""
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'return.order') or ('New')
        result = super(ReturnOrder, self).create(vals)
        return result

    @api.multi
    def action_returned_cancel(self):
        self.write({'state': 'returned_cancel'})
        self.account_invoice_ids.action_invoice_cancel()
        self.stock_move_ids.mapped('move_ids_without_package').write({
            'state': 'cancel'
        })
        stock_quant = self.env['stock.quant']
        for line in self.stock_move_ids.move_line_ids_without_package:
            quant = stock_quant.search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', line.location_dest_id.id)
            ])
            quant.sudo().quantity -= line.qty_done
            quant = stock_quant.search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', line.location_id.id)
            ])
            quant.sudo().quantity += line.qty_done
            line.qty_done = 0
        self.stock_move_ids.write({'state': 'cancel'})


class ReturnOrderLine(models.Model):
    """Class created to add return order line."""

    _name = 'return.order.line'
    _description = 'Return Order Line'

    @api.onchange('product_id')
    def onchange_product(self):
        """Onchange call when customer is not selected."""
        if self.return_id.type_partner == 'customer':
            if not self.return_id.partner_id or \
                    not self.return_id.pricelist_id:
                raise ValidationError("Please select Customer first!")

    @api.depends('qty', 'unit_price', 'tax_id')
    def _compute_amount(self):
        """Compute the amounts of the Order line."""
        for line in self:
            price = line.unit_price * (1 - 0.0 / 100.0)
            taxes = line.tax_id.compute_all(
                price, line.sale_order_id.currency_id, line.qty,
                product=line.product_id,
                partner=line.sale_order_id.partner_shipping_id)
            if taxes:
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get(
                        'taxes', [])),
                    'value_before_tax': line.unit_price * line.qty
                })
                line.update({
                    'value': taxes['total_included']})
            else:
                order_line_rec = line.sale_order_id.mapped('order_line').filtered(
                    lambda p: p.product_id == line.product_id)
                line.update({
                    'value': order_line_rec.price_subtotal})

    # Defined fields
    price_tax = fields.Float(
        tring='Total Tax', readonly=True, compute='_compute_amount',
        store=True)
    return_id = fields.Many2one("return.order", string="Return")
    sale_type = fields.Selection(
        [('sale', 'Sale Order')], default='sale', required=True)
    product_id = fields.Many2one("product.product", string="Product")
    sale_order_id = fields.Many2one(
        "sale.order", string="Sale Order", required=0, copy=False)
    invoice_id = fields.Many2many(
        "account.invoice", string="Invoice", readonly=1, store=1)
    stock_move_id = fields.Many2many(
        "stock.move", string="Stock Move", readonly=1, store=1)
    unit_price = fields.Float(string="Unit Price", readonly=0)
    qty = fields.Float(string="Quantity", readonly=0)
    currency_id = fields.Many2one('res.currency')
    value = fields.Monetary(
        string="Subtotal", store=True, currency_field='currency_id')
    value_before_tax = fields.Float(
        string="Total", currency_field='currency_id',
        compute='_compute_amount')
    tax_id = fields.Many2many(
        "account.tax", string="Tax")
    purchase_order_id = fields.Many2one(
        "purchase.order", string="Purchase Order")
    vendor_id = fields.Many2one(
        "res.partner", string="Vendor", related='purchase_order_id.partner_id',
        readonly=1)
    return_option = fields.Selection([
        ('stock', 'Return to Stock')], default="stock")
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')], default='draft', readonly=1)
    partner_id = fields.Many2one(
        "res.partner", string="Customer", related='return_id.partner_id')
    manufacturer_partner_id = fields.Many2one(
        'res.partner', string='Manufacturer')
    """ Add filed name & display_type for Add note selection"""
    name = fields.Text(string='Description')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    sequence = fields.Integer(string='Sequence', default=10)

    @api.onchange('product_id')
    def _onchange_product_get_so_po(self):
        if self._context.get('active_model') == 'sale.order' and \
                self._context.get('active_id'):
            sale_id = self.env['sale.order'].browse(self._context.get(
                'active_id'))
            return {'domain': {'sale_order_id': [('id', 'in', sale_id.ids)]}}
        for record in self:
            # Get value of order line fields from So or Without SO
            record.name = record.product_id.description
            if record.return_id.type_partner == 'customer':
                if record.sale_order_id:
                    record.sale_order_id = False
                sales_order_line = self.env['sale.order.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('return_order_id', '=', False),
                    ('order_id.state', '=', 'sale')
                ])
                order_line_rec = sales_order_line.filtered(
                    lambda x: x.order_id and
                              x.order_id.partner_id == record.return_id.partner_id)
                sales_order = list(set(
                    [line.order_id.id for line in order_line_rec]))
                # Value of order line without SO
                if not sales_order:
                    product = record.product_id
                    record.unit_price = self.env[
                        'account.tax']._fix_tax_included_price_company(
                        self._get_display_price(
                            product), product.taxes_id,
                        record.tax_id, self.env.user.company_id)
                    taxes = record.product_id.taxes_id
                    record.tax_id = record.return_id.partner_id.property_account_position_id.map_tax(taxes, record.product_id, record.return_id.partner_id)
                # passed sales order based on products and partner.
                if sales_order:
                    return {'domain': {'sale_order_id': [
                        ('id', 'in', sales_order)]}}
                else:
                    return {'domain': {'sale_order_id': [
                        ('id', '=', False)]}}
            # Get value of order line from PO or without PO.
            else:
                if record.purchase_order_id:
                    record.purchase_order_id = False
                purchase_order_line = self.env['purchase.order.line'].search(
                    [('product_id', '=', record.product_id.id),
                     ('return_order_id', '=', False),
                     ('order_id.state', '=', 'purchase')])
                purchase_order_line_rec = purchase_order_line.filtered(
                    lambda p: p.order_id and
                              p.order_id.partner_id == record.return_id.supplier_id)
                purchase_order = list(set(
                    [line.order_id.id for line in purchase_order_line_rec]))
                # Value when no PO
                if not purchase_order:
                    product = record.product_id
                    record.unit_price = record.product_id.standard_price
                    taxes = record.product_id.taxes_id
                    record.tax_id = record.return_id.supplier_id.property_account_position_id.map_tax(
                        taxes, record.product_id, record.return_id.supplier_id)
                # passed purchase order value based on product and vendor.
                if purchase_order:
                    return {'domain': {'purchase_order_id': [
                        ('id', 'in', purchase_order)]}}
                else:
                    return {'domain': {'purchase_order_id': [
                        ('id', '=', False)]}}

    @api.onchange('product_id')
    def _onchange_product_value(self):
        if self._context.get('active_model') == 'sale.order' and \
                self._context.get('active_id'):
            for record in self:
                order_line = record.sale_order_id.mapped(
                    'order_line').filtered(
                    lambda p: p.product_id == record.product_id)
                total_qty = 0.00
                if order_line:
                    for rec in order_line:
                        total_qty += (rec.product_uom_qty - rec.return_qty)
                        record.unit_price = rec.price_unit
                        record.tax_id = rec.tax_id
                    record.qty = total_qty

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Onchange call to get price, tax value from so."""
        for record in self:
            order_line = record.sale_order_id.mapped('order_line').filtered(
                lambda p: p.product_id == record.product_id)
            total_qty = 0.00
            if order_line:
                for rec in order_line:
                    total_qty += (rec.product_uom_qty - rec.return_qty)
                    record.unit_price = rec.price_unit
                    record.tax_id = rec.tax_id
                record.qty = total_qty
        self.invoice_id = [
            (6, 0, [record.id for record in self.env['account.invoice'].search(
                [('origin', 'ilike', self.sale_order_id.name)],
                limit=1) if record])]
        if self.sale_order_id:
            self.stock_move_id = [
                (6, 0, [record.id for record in self.env['stock.move'].search(
                    [('origin', '=', self.sale_order_id.name)],
                    limit=1) if record])]
        if self._context.get('active_model') == 'sale.order' and \
                self._context.get('active_id'):
            order_line_rec = self.sale_order_id.order_line.filtered(
                lambda s: not s.return_order_id)
            product_ids = order_line_rec.mapped('product_id').ids
            return {'domain': {'product_id': [('id', 'in', product_ids)]}}

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order(self):
        """Onchange call to get price and tax value from PO."""
        for record in self:
            if record.return_id.type_partner == 'supplier':
                order_line = record.purchase_order_id.mapped(
                    'order_line').filtered(
                    lambda p: p.product_id == record.product_id)
                total_qty = 0.00
                if order_line:
                    for rec in order_line:
                        total_qty += (rec.product_uom_qty - rec.return_qty)
                        record.unit_price = rec.price_unit
                        record.tax_id = rec.taxes_id
                    record.qty = total_qty

    @api.multi
    def _get_display_price(self, product):
        """Function to set product's unit price as per pricelist."""
        if self.return_id.type_partner == 'customer':
            if self.return_id.partner_id.id:
                if self.return_id.pricelist_id.discount_policy == 'with_discount':
                    return product.with_context(
                        pricelist=self.return_id.pricelist_id.id).price
                product_context = dict(
                    self.env.context, partner_id=self.return_id.partner_id.id,
                    date=self.return_id.date, uom=self.product_id.uom_id.id)

                final_price, rule_id = self.return_id.pricelist_id.with_context(
                    product_context).get_product_price_rule(
                    self.product_id, self.qty or 1.0,
                    self.return_id.partner_id)
                base_price, currency = self.with_context(
                    product_context)._get_real_price_currency(
                    product, rule_id, self.qty, self.product_id.uom_id,
                    self.return_id.pricelist_id.id)
                if currency != self.return_id.pricelist_id.currency_id:
                    base_price = currency._convert(
                        base_price, self.return_id.pricelist_id.currency_id,
                        self.return_id.company_id or self.env.user.company_id,
                        self.return_id.date or fields.Date.today())
                return max(base_price, final_price)

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('display_type', self.default_get(['display_type'])['display_type']):
                values.update(product_id=False, unit_price=0, qty=0, value_before_tax=0)

        return super(ReturnOrderLine, self).create(vals_list)

    # _sql_constraints = [
    #     ('accountable_required_fields',
    #         "CHECK(display_type IS NOT NULL OR product_id IS NOT NULL)",
    #         "Missing required fields on accountable return order line."),
    #     ('non_accountable_null_fields',
    #         "CHECK(display_type IS NULL OR (product_id IS NULL AND unit_price = 0 AND qty = 0 AND value_before_tax = 0))",
    #         "Forbidden values on non-accountable return order line"),
    # ]

    @api.multi
    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a return order line. Instead you should delete the current line and create a new line of the proper type."))
        return super(ReturnOrderLine, self).write(values)


class StockMove(models.Model):
    """Class inherit to add field."""

    _inherit = 'stock.picking'

    return_order_id = fields.Many2one('return.order', string="Return Order")


class AccountInvoice(models.Model):
    """Class inherit to add field."""

    _inherit = 'account.invoice'

    return_order_id = fields.Many2one(
        'return.order', string="Return Reference")


class SalesOrderLine(models.Model):
    """Class inherit to add field."""

    _inherit = 'sale.order.line'

    return_order_id = fields.Many2one(
        'return.order', string="Return Reference", copy=False)
    return_qty = fields.Float(string="Return Qty", readonly=1, copy=False)
    all_return = fields.Boolean(string="All Return", default=False, copy=False)


class PurchaseOrderLine(models.Model):
    """Class inherit to add field."""

    _inherit = 'purchase.order.line'

    return_order_id = fields.Many2one(
        'return.order', string="Return Reference", copy=False)
    return_qty = fields.Float(string="Return Qty", readonly=1, copy=False)
    all_return = fields.Boolean(string="All Return", default=False, copy=False)
