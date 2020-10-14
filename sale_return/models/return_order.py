from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date


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
        ('cancel', 'Cancelled'),
        ('done', 'Done')], default='draft',
        required=True, track_visibility='always')
    credit_invoice_id = fields.Many2one(
        "account.invoice", string="Credit Invoice", track_visibility='always')
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount', currency_field='currency_id', store=True,
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

    @api.onchange('partner_id')
    def onchange_partner(self):
        """Onchange call for customer pricelist."""
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
        }
        self.update(values)

    @api.depends('line_ids.value_before_tax')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.line_ids:
                amount_untaxed += line.value_before_tax
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

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
        self.write({'state': 'cancel'})

    @api.multi
    def process_return(self):
        """Main method to process return according the return option."""
        self.check_orderline()
        # self.check_delivery_status()
        if self.type_partner == 'customer':
            line_ids_wo_so = self.line_ids.sudo().filtered(
                lambda l: not l.sale_order_id)
            if line_ids_wo_so:
                for record in line_ids_wo_so:
                    if record.return_option == 'scrap':
                        self.process_scrap(line=record)
                    elif record.return_option == 'no_return':
                        self.process_no_return()
                    elif record.return_option == 'manufacturer':
                        self.process_return_to_vendor_wo_po(lines=record)
                        self.process_refund_customer_wo_so(lines=record)
                    elif record.return_option == 'stock':
                        self.process_return_without_so(lines=line_ids_wo_so)
                        self.process_refund_customer_wo_so(
                            lines=line_ids_wo_so)

            line_ids = self.env['return.order.line'].sudo().search(
                [('return_id', '=', self.id), ('sale_order_id', '!=', False)])
            if line_ids:
                for record in line_ids:
                    if record.return_option == 'scrap':
                        self.process_scrap(line=record)
                    elif record.return_option == 'no_return':
                        self.process_no_return()
                    elif record.return_option == 'manufacturer':
                        self.process_return_to_vendor_wo_po(lines=record)
                        self.process_refund_customer_wo_so(lines=record)
                    elif record.return_option == 'stock':
                        if record.sale_order_id:
                            self.process_return_to_stock(line=record)

            if not any(line.state not in ['done'] for line in self.line_ids):
                self.sudo().write({'state': 'done'})
        else:
            line_ids_wo_po = self.line_ids.sudo().filtered(
                lambda l: not l.purchase_order_id)
            if line_ids_wo_po:
                for record in line_ids_wo_po:
                    if record.return_option_po == 'stock':
                        self.process_restun_product_vendor_type(lines=record)
                        self.product_refund_from_vendor_type(lines=record)
            line_ids = self.line_ids.sudo().filtered(
                lambda l: l.purchase_order_id)
            if line_ids:
                for record in line_ids:
                    if record.return_option_po == 'stock':
                        self.process_return_product_vendor_with_po(
                            lines=record)

    def process_return_product_vendor_with_po(self, lines):
        """Function call to create retun to vendor with PO."""
        for record in lines:
            refund = self.env['account.invoice'].create({
                'type': 'in_refund',
                'partner_id': self.supplier_id.id,
                'return_order_id': self.id})
        for line in lines:
            # invoice_line_id =
            self.env['account.invoice.line'].create({
                'name': line.product_id.name or '',
                'product_id': line.product_id.id or False,
                'account_id': line.product_id.property_account_income_id.id \
                or line.product_id.categ_id.property_account_income_categ_id.id \
                or False,
                'quantity': line.qty or 0.0,
                'uom_id': line.product_id.product_tmpl_id.uom_id.id or False,
                'price_unit': line.unit_price or 0.0,
                'invoice_line_tax_ids': line.tax_id.ids or False,
                'invoice_id': refund and refund.id or False})

        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming')], limit=1)
        picking_id = self.env['stock.picking'].search(
            [('group_id', '=', lines.purchase_order_id.group_id.id),
             ('product_id', '=', lines.product_id.id),
             ('picking_type_id', '=', picking_type_id.id),
             ('state', '=', 'done')], limit=1)
        if picking_id:
            vals = self.env['stock.return.picking'].with_context({
                'active_id': picking_id.id}).default_get(
                ['product_return_moves', 'move_dest_exists',
                    'parent_location_id',
                 'original_location_id', 'location_id', ])
            actual_line = False
            if 'product_return_moves' in vals:
                actual_line = [return_data for return_data in vals[
                    'product_return_moves'] if
                    return_data[2]['product_id'] == lines.product_id.id]
            if actual_line:
                stock_return_vendor = self.env['stock.return.picking']
                default_data = stock_return_vendor.with_context(
                    active_ids=picking_id.ids,
                    active_id=picking_id.ids[0]).default_get(
                    ['move_dest_exists', 'original_location_id',
                        'product_return_moves', 'parent_location_id',
                     'location_id'])
                default_data.pop('product_return_moves')
                actual_line[0][2]['quantity'] = lines.qty
                default_data['product_return_moves'] = actual_line
                return_wiz = stock_return_vendor.with_context(
                    active_ids=picking_id.ids,
                    active_id=picking_id.ids[0]).create(
                    default_data)
                return_wiz.product_return_moves.sudo().write({
                    'quantity': lines.qty, 'to_refund': True})
                res = return_wiz.sudo().create_returns()
                return_pick = self.env['stock.picking'].sudo().browse(
                    res['res_id'])
                # Validate picking
                return_picking_type_id = self.env[
                    'stock.picking.type'].search(
                    [('code', '=', 'incoming')], limit=1)
                stock_picking_ids = self.env['stock.picking'].search(
                    [('group_id', '=', lines.purchase_order_id.group_id.id),
                     ('picking_type_id', '=',
                        return_picking_type_id.id)])
                self.stock_move_ids = [(4, stock_picking_ids.id)]
                return_pick.move_line_ids.write({
                    'qty_done': lines.qty, 'to_refund': True})
                return_pick.button_validate()
            lines.write({'state': 'done'})
            return_pick.sudo().write({'return_order_id': self.id})
            self.write({'state': 'done'})

    def process_restun_product_vendor_type(self, lines=None):
        """Function call to return product to vendor when type is vendor."""
        for record in lines:
            if record.return_option_po == 'stock':
                picking_type_id = self.env['stock.picking.type'].sudo().search([
                    ('code', '=', 'outgoing')], limit=1)
                location = self.env['stock.location'].search(
                    [('usage', '=', 'supplier')], limit=1)
                picking_return = self.env['stock.picking'].sudo().create({
                    'picking_type_id': picking_type_id.id or False,
                    'partner_id': self.supplier_id.id,
                    'location_id': picking_type_id.default_location_src_id.id,
                    'location_dest_id': location.id,
                    'return_order_id': self.id})
                for line in record:
                    self.env['stock.move'].sudo().create({
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_id.product_tmpl_id.uom_id.id,
                        'product_uom_qty': line.qty,
                        'location_id': picking_type_id.default_location_src_id.id,
                        'location_dest_id': location.id,
                        'partner_id': self.supplier_id.id,
                        'picking_id': picking_return.id,
                        'picking_type_id': picking_type_id.id,
                        'quantity_done': line.qty})
                    line.sudo().write({'state': 'done'})
                if picking_return:
                    picking_return.sudo().write(
                        {'return_order_id': self.id})
                    picking_return.sudo().action_confirm()
                    picking_return.sudo().action_assign()
                    picking_return.sudo().button_validate()
                self.sudo().write({'state': 'done'})

    def product_refund_from_vendor_type(self, lines):
        """Method to create refund note without PO."""
        refund = self.env['account.invoice'].create({
            'type': 'in_refund',
            'partner_id': self.supplier_id.id,
            'return_order_id': self.id})
        for line in lines:
            # invoice_line_id =
            self.env['account.invoice.line'].create({
                'name': line.product_id.name or '',
                'product_id': line.product_id.id or False,
                'account_id': line.product_id.property_account_income_id.id \
                or line.product_id.categ_id.property_account_income_categ_id.id \
                or False,
                'quantity': line.qty or 0.0,
                'uom_id': line.product_id.product_tmpl_id.uom_id.id or False,
                'price_unit': line.unit_price or 0.0,
                'invoice_line_tax_ids': line.tax_id.ids or False,
                'invoice_id': refund and refund.id or False})

    def process_return_to_vendor_wo_po(self, lines=None):
        """Function call to retun product to manuf without SO/PO."""
        manufacturer_partner_id = False
        for line in lines:
            if line.return_option == 'manufacturer':
                manufacturer_partner_id = line.manufacturer_partner_id.id
        picking_type_id = self.env['stock.picking.type'].sudo().search([
            ('code', '=', 'incoming')], limit=1)
        location = self.env['stock.location'].search(
            [('usage', '=', 'supplier')], limit=1)
        picking_return = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type_id.id or False,
            'partner_id': manufacturer_partner_id or self.partner_id.id,
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id': location.id,
            'return_order_id': self.id})
        for line in lines:
            # stock_move_id =
            self.env['stock.move'].sudo().create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.product_tmpl_id.uom_id.id,
                'product_uom_qty': line.qty,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': location.id,
                'partner_id': self.partner_id.id,
                'picking_id': picking_return.id,
                'picking_type_id': picking_type_id.id,
                'quantity_done': line.qty})
            line.sudo().write({'state': 'done'})
        if picking_return:
            picking_return.sudo().write({'return_order_id': self.id})
            picking_return.sudo().action_confirm()
            picking_return.sudo().action_assign()
            picking_return.sudo().button_validate()
        self.sudo().write({'state': 'done'})

    def process_return_without_so(self, lines=None):
        """Method to process return order record without so."""
        manufacturer_partner_id = False
        for line in lines:
            if line.return_option == 'manufacturer':
                manufacturer_partner_id = line.manufacturer_partner_id.id
        picking_type_id = self.env['stock.picking.type'].sudo().search([
            ('code', '=', 'incoming')], limit=1)
        picking_return = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type_id.id or False,
            'partner_id': manufacturer_partner_id or self.partner_id.id,
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'return_order_id': self.id})
        for line in lines:
            # stock_move_id =
            self.env['stock.move'].sudo().create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.product_tmpl_id.uom_id.id,
                'product_uom_qty': line.qty,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
                'partner_id': self.partner_id.id,
                'picking_id': picking_return.id,
                'picking_type_id': picking_type_id.id,
                'quantity_done': line.qty})
            line.sudo().write({'state': 'done'})
        if picking_return:
            picking_return.sudo().write({'return_order_id': self.id})
            picking_return.sudo().action_confirm()
            picking_return.sudo().action_assign()
            picking_return.sudo().button_validate()
        self.sudo().write({'state': 'done'})

    def process_scrap(self, line=None):
        """Method to create return order record in stock scrap."""
        self.check_orderline()
        line_record = self.line_ids
        for record in line_record:
            if record.return_option == "scrap":
                product = record.product_id
                product_id = record.product_id.id
                quantity = record.qty
                source_document = record.sale_order_id.name
                scrap = self.env['stock.scrap'].create(
                    {'product_id': product_id,
                     'scrap_qty': quantity,
                     'origin': source_document,
                     'product_uom_id': product.uom_id.id
                     })
                scrap.action_validate()
                self.process_return_to_stock(line)
                scrap.do_scrap()
                self.write({'state': 'done'})
                record.write({'state': 'done'})
                record.sale_order_id.write({'state': 'return'})

    def process_no_return(self):
        """Function call when no return."""
        self.check_orderline()
        line_record = self.line_ids.filtered(
            lambda m: m.return_option == 'no_return')
        if line_record:
            for record in line_record:
                record.write({'state': 'done'})
            self.write({'state': 'done'})
            record.sale_order_id.write({'state': 'return'})
            return True

    def process_refund_customer_wo_so(self, lines=None):
        """Method to create credit note record without so."""
        credit_note = self.env['account.invoice'].create({
            'type': 'out_refund',
            'partner_id': self.partner_id.id,
            'return_order_id': self.id})
        for line in lines:
            # invoice_line_id =
            self.env['account.invoice.line'].create({
                'name': line.product_id.name or '',
                'product_id': line.product_id.id or False,
                'account_id': line.product_id.property_account_income_id.id \
                or line.product_id.categ_id.property_account_income_categ_id.id \
                or False,
                'quantity': line.qty or 0.0,
                'uom_id': line.product_id.product_tmpl_id.uom_id.id or False,
                'price_unit': line.unit_price or 0.0,
                'invoice_line_tax_ids': line.tax_id.ids or False,
                'invoice_id': credit_note and credit_note.id or False})

    def process_refund_customer(self, line=None):
        """Function call to refund customer."""
        line_record_stock = self.line_ids.filtered(
            lambda m: m.return_option == 'stock' and m.sale_order_id)
        for record in line_record_stock:
            invoice_ids_customer = record.sale_order_id.invoice_ids.filtered(
                lambda m: m.state not in ['draft', 'cancelled'])
            if not invoice_ids_customer:
                raise ValidationError(
                    "Please create a Invoice of this Sale Order first!")

            # Make a credit note customer
            credit_note_wizard = self.env[
                'account.invoice.refund'].with_context(
                {'active_ids': invoice_ids_customer.ids}).create(
                {'filter_refund': 'refund',
                    'description': self.reason_id.name})
            # Check the result
            credit_invoice = credit_note_wizard.invoice_refund()
            credit_note_domain = credit_invoice.get('domain')[1]
            inv_id = self.env['account.invoice'].search([credit_note_domain])
            for invoice in inv_id:
                for invoice_line in invoice.invoice_line_ids:
                    if invoice_line.product_id == line.product_id:

                        invoice_line.update({
                            "quantity": line.qty,
                            "price_unit": line.unit_price})
                    else:
                        # unlink invoice line which does not contains line
                        # products
                        invoice_line.sudo().unlink()
                    self.account_invoice_ids = [(4, invoice.id)]

    def process_return_to_stock(self, line=None):
        """Method to process return order record."""
        self.check_orderline()
        line_record_stock = self.line_ids.sudo().filtered(
            lambda m: m.return_option == 'stock' and m.sale_order_id)
        self.process_refund_customer(line)
        picking_type_id = self.env['stock.picking.type'].sudo().search([
            ('code', '=', 'outgoing'),
            ('warehouse_id', '=', line.sale_order_id.warehouse_id.id)])
        picking_id = self.env['stock.picking'].sudo().search(
            [('group_id', '=', line.sale_order_id.procurement_group_id.id),
             ('product_id', '=', line.product_id.id),
             ('picking_type_id', '=', picking_type_id.id),
             ('state', '=', 'done')], limit=1)
        if picking_id:
            vals = self.env['stock.return.picking'].with_context({
                'active_id': picking_id.id}).default_get(
                ['product_return_moves', 'move_dest_exists',
                    'parent_location_id',
                 'original_location_id', 'location_id', ])
            actual_line = False
            if 'product_return_moves' in vals:
                actual_line = [return_data for return_data in vals['product_return_moves'] if
                               return_data[2]['product_id'] == line.product_id.id]

            if actual_line:
                return_picking_id = self.env[
                    'stock.return.picking'].sudo().create(vals)
                StockReturnPicking = self.env['stock.return.picking']

                default_data = StockReturnPicking.with_context(
                    active_ids=picking_id.ids,
                    active_id=picking_id.ids[0]).default_get(
                    ['move_dest_exists', 'original_location_id',
                        'product_return_moves', 'parent_location_id',
                     'location_id'])
                default_data.pop('product_return_moves')
                actual_line[0][2]['quantity'] = line.qty
                default_data['product_return_moves'] = actual_line
                return_wiz = StockReturnPicking.with_context(
                    active_ids=picking_id.ids,
                    active_id=picking_id.ids[0]).create(
                    default_data)
                return_wiz.product_return_moves.sudo().write({
                    'quantity': line.qty, 'to_refund': True})
                res = return_wiz.sudo().create_returns()
                return_pick = self.env['stock.picking'].sudo().browse(
                    res['res_id'])
                # Validate picking
                return_picking_type_id = self.env['stock.picking.type'].sudo().search([
                    ('code', '=', 'incoming'),
                    ('warehouse_id', '=', line.sale_order_id.warehouse_id.id)])
                pickings = self.env['stock.picking'].sudo().search(
                    [('group_id', '=', line.sale_order_id.procurement_group_id.id),
                     ('picking_type_id', '=', return_picking_type_id.id)])
                if pickings:
                    self.stock_move_ids = [(4, picking.id, None) for picking in pickings]
                # self.stock_move_ids = [(6, 0, [record.id for record in self.env['stock.picking'].search(
                #     [('group_id', '=', line.sale_order_id.procurement_group_id.id),
                #      ('picking_type_id', '=', return_picking_type_id.id)]) if record])]
                return_pick.move_line_ids.sudo().write({
                    'qty_done': line.qty, 'to_refund': True})
                return_pick.sudo().button_validate()
            line.sudo().write({'state': 'done'})
            line.sale_order_id.sudo().write({'state': 'return'})
            self.sudo().write({'state': 'done'})

    def process_return_to_vendor(self, line=None):
        """Method to process return to vendor(Closed this as of now)."""
        line_record = self.line_ids.filtered(
            lambda m: m.return_option == 'manufacturer')
        self.check_orderline()
        self.process_return_to_stock(line)
        for record in line_record:
            invoice_id = record.purchase_order_id.invoice_ids
            if not invoice_id:
                raise ValidationError(
                    "Please create a Bill of this Purchase Order first!")
            invoice_ids_customer = record.sale_order_id.invoice_ids
            # if not invoice_ids_customer:
            #     raise ValidationError("Please create a Invoice of this Sale Order first!")

            # Make a credit note
            credit_note_ids = credit_note_wizard = self.env[
                'account.invoice.refund'].with_context(
                {'active_ids': invoice_id.ids}).create({
                    'filter_refund': 'refund',
                    'description': self.reason_id.name})
            # Check the result
            credit_invoice = credit_note_wizard.invoice_refund()
            credit_note_domain = credit_invoice.get('domain')[1]
            inv_id = self.env['account.invoice'].search([credit_note_domain])
            for invoice in inv_id:
                for invoice_line in invoice.invoice_line_ids:
                    if invoice_line.product_id == line.product_id:
                        invoice_line.update({
                            "quantity": line.qty,
                            "price_unit": line.unit_price})
                    self.account_invoice_ids = [(4, invoice.id)]

        if not self.line_ids.filtered(lambda m: m.purchase_order_id):
            raise ValidationError("""Can not return to the vendor as there is
                no purchase order linked to this order!""")

        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming')], limit=1)

        picking_id = self.env['stock.picking'].search(
            [('group_id', '=', line.purchase_order_id.group_id.id),
             ('product_id', '=', line.product_id.id),
             ('picking_type_id', '=', picking_type_id.id),
             ('state', '=', 'done')], limit=1)
        if picking_id:
            vals = self.env['stock.return.picking'].with_context(
                {'active_id': picking_id.id}).default_get(
                ['product_return_moves', 'move_dest_exists',
                    'parent_location_id',
                 'original_location_id', 'location_id', ])
            actual_line = False
            if 'product_return_moves' in vals:
                actual_line = [return_data for return_data in vals['product_return_moves'] if
                               return_data[2]['product_id'] == line.product_id.id]
            if actual_line:
                return_picking_id = self.env[
                    'stock.return.picking'].create(vals)
                StockReturnPicking = self.env['stock.return.picking']
                default_data = StockReturnPicking.with_context(
                    active_ids=picking_id.ids,
                    active_id=picking_id.ids[0]).default_get(
                    ['move_dest_exists', 'original_location_id',
                        'product_return_moves', 'parent_location_id',
                     'location_id'])
                default_data.pop('product_return_moves')
                actual_line[0][2]['quantity'] = line.qty
                default_data['product_return_moves'] = actual_line
                return_wiz = StockReturnPicking.with_context(
                    active_ids=picking_id.ids,
                    active_id=picking_id.ids[0]).create(
                    default_data)
                return_wiz.product_return_moves.write({
                    'quantity': line.qty, 'to_refund': True})

                res = return_wiz.create_returns()
                return_pick = self.env['stock.picking'].browse(res['res_id'])

                # Validate picking
                # Return picking for sale order
                sale_return_picking_type_id = self.env['stock.picking.type'].search([
                    ('code', '=', 'incoming'), ('warehouse_id', '=', line.sale_order_id.warehouse_id.id)])
                self.stock_move_ids = [(6, 0, [
                    record.id for record in self.env['stock.picking'].search(
                        [('group_id', '=',
                            line.sale_order_id.procurement_group_id.id),
                            ('picking_type_id', '=',
                                sale_return_picking_type_id.id)]) if record])]

                # Return picking for purchase order
                purchase_return_picking_type_id = self.env['stock.picking.type'].search([
                    ('code', '=', 'outgoing'),
                    ('warehouse_id', '=', line.sale_order_id.warehouse_id.id)])
                stock_picking_ids = self.env['stock.picking'].search(
                    [('group_id', '=', line.purchase_order_id.group_id.id),
                     ('picking_type_id', '=',
                        purchase_return_picking_type_id.id)])
                self.stock_move_ids = [(4, stock_picking_ids.id)]
                return_pick.move_line_ids.write({
                    'qty_done': line.qty, 'to_refund': True})
                return_pick.button_validate()
            line.write({'state': 'done'})
            line.sale_order_id.write({'state': 'return'})
            self.write({'state': 'done'})

    def check_orderline(self):
        """Method to check if there is orderline or not."""
        if not self.line_ids:
            raise ValidationError("""Cannot process return as there is no order line
                associated with this record!""")

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


class ReturnOrderLine(models.Model):
    """Class created to add return order line."""

    _name = 'return.order.line'
    _description = 'Return Order Line'

    @api.onchange('product_id')
    def onchange_product(self):
        """Onchange call when customer is not selected."""
        if self.return_id.type_partner == 'customer':
            if not self.return_id.partner_id or not self.return_id.pricelist_id:
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
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get(
                    'taxes', [])),
                'value': taxes['total_included'],
                'value_before_tax': line.unit_price * line.qty
            })

    # Defined fields
    price_tax = fields.Float(
        compute='_compute_amount', string='Total Tax',
        readonly=True, store=True)
    return_id = fields.Many2one("return.order", string="Return")
    sale_type = fields.Selection(
        [('sale', 'Sale Order')], default='sale', required=True)
    product_id = fields.Many2one("product.product", string="Product")
    sale_order_id = fields.Many2one(
        "sale.order", string="Sale Order", required=0)
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
        string="Total", currency_field='currency_id')
    tax_id = fields.Many2many(
        "account.tax", string="Tax", compute="calculate_tax")
    purchase_order_id = fields.Many2one(
        "purchase.order", string="Purchase Order")
    vendor_id = fields.Many2one(
        "res.partner", string="Vendor", related='purchase_order_id.partner_id',
        readonly=1)
    return_option = fields.Selection([
        ('stock', 'Return to Stock'),
        ('manufacturer', 'Returns to Manufacturer'),
        ('scrap', 'Scrap'),
        ('no_return', 'No Return')])
    return_option_po = fields.Selection([
        ('stock', 'Return to Stock')], string="Return Option", default="stock")
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')], default='draft', readonly=1)
    partner_id = fields.Many2one(
        "res.partner", string="Customer", related='return_id.partner_id')
    manufacturer_partner_id = fields.Many2one(
        'res.partner', string='Manufacturer')

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order(self):
        if self.return_id.type_partner == 'supplier':
            if self.purchase_order_id:
                product_ids = self.purchase_order_id.order_line.mapped(
                    'product_id').ids
                return {'domain': {'product_id': [('id', 'in', product_ids)]}}

    @api.onchange('sale_order_id')
    def _onchange_order_id(self):
        if self.sale_order_id:
            product_ids = self.sale_order_id.order_line.mapped(
                'product_id').ids
            return {'domain': {'product_id': [('id', 'in', product_ids)]}}

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        self.value = self.sale_order_id.amount_total
        self.qty = self.unit_price = self.product_id = None
        self.invoice_id = [
            (6, 0, [record.id for record in self.env['account.invoice'].search(
                [('origin', 'ilike', self.sale_order_id.name)],
                limit=1) if record])]
        if self.sale_order_id:
            self.stock_move_id = [
                (6, 0, [record.id for record in self.env['stock.move'].search(
                    [('origin', '=', self.sale_order_id.name)],
                    limit=1) if record])]

    @api.depends('product_id')
    def calculate_tax(self):
        """Function call to calculate tax."""
        for record in self:
            order_line_rec = record.sale_order_id.mapped(
                'order_line').filtered(
                lambda p: p.product_id == record.product_id)
            for rec in order_line_rec:
                record.unit_price = rec.price_unit
                record.tax_id = rec.tax_id

    @api.onchange('product_id')
    def onchange_product_id(self):
        """Function call to get qty of product."""
        for record in self:
            if record.return_id.type_partner == 'customer':
                if record.return_option == 'manufacturer' and record.sale_order_id:
                    manuf_ids = self.product_id.seller_ids.mapped(
                        'name').ids
                    return {'domain': {'manufacturer_partner_id': [('id', 'in', manuf_ids)]}}
                order_line_rec = record.sale_order_id.mapped(
                    'order_line').filtered(
                    lambda p: p.product_id == record.product_id)
                for reco in order_line_rec:
                    record.qty = reco.product_uom_qty
                    self.purchase_order_id = self.env['purchase.order'].search(
                        [('origin', '=', self.sale_order_id.name),
                            ('product_id', '=', reco.product_id.id)], limit=1)
                if not record.sale_order_id:
                    print("\n\n !!!", record.sale_order_id)
                    product = self.product_id
                    self.unit_price = self.env[
                        'account.tax']._fix_tax_included_price_company(
                            self._get_display_price(
                                product), product.taxes_id,
                            self.tax_id, self.env.user.company_id)
            else:
                if not record.purchase_order_id:
                    self.unit_price = record.product_id.standard_price
                if record.purchase_order_id:
                    order_line_rec = record.purchase_order_id.mapped(
                        'order_line').filtered(
                        lambda p: p.product_id == record.product_id)
                    for reco in order_line_rec:
                        record.qty = reco.product_qty
                        self.unit_price = reco.price_unit

    @api.multi
    def _get_display_price(self, product):
        """ Function to set product's unit price as per pricelist """
        if self.return_id.type_partner == 'customer':
            if self.return_id.pricelist_id.discount_policy == 'with_discount':
                return product.with_context(pricelist=self.return_id.pricelist_id.id).price
            product_context = dict(self.env.context, partner_id=self.return_id.partner_id.id, date=self.return_id.date, uom=self.product_id.uom_id.id)

            final_price, rule_id = self.return_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.qty or 1.0, self.return_id.partner_id)
            base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.qty, self.product_id.uom_id, self.return_id.pricelist_id.id)
            if currency != self.return_id.pricelist_id.currency_id:
                base_price = currency._convert(
                    base_price, self.return_id.pricelist_id.currency_id,
                    self.return_id.company_id or self.env.user.company_id, self.return_id.date or fields.Date.today())
            return max(base_price, final_price)

class StockMove(models.Model):
    """Class inherit to add field."""

    _inherit = 'stock.picking'

    return_order_id = fields.Many2one('return.order', string="Return Order")


class AccountInvoice(models.Model):
    """Class inherit to add field."""

    _inherit = 'account.invoice'

    return_order_id = fields.Many2one('return.order')
