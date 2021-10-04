from odoo import fields, models, _, api
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools import float_round
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    """Class Inherit for added some functionality."""

    _inherit = 'sale.order'

    user_id = fields.Many2one(
        'res.users', string='Salesperson',
        index=True, track_visibility='onchange',
        track_sequence=2, default=lambda self: self.env.user,
        domain=[('is_salesperson', '=', True)])
    confirmation_date = fields.Datetime(
        string='Confirmation Date',
        readonly=True, index=True,
        help="Date on which the sales order is confirmed.",
        oldname="date_confirm", copy=False, track_visibility='onchange')

    def price_updates(self, values):
        """Update products prices when change the partner."""
        for line in self.order_line:
            line.product_id_change()

    @api.model
    def create(self, vals):
        """Function override to pass sales person on readonly field."""
        res = super(SaleOrder, self).create(vals)
        if res.partner_id.user_id:
            res.user_id = res.partner_id.user_id.id
        else:
            res.user_id = self.env.user
        return res

    @api.multi
    def write(self, values):
        """Function call to pass sales person value."""
        if 'partner_id' in values:
            partner_id = self.env['res.partner'].browse(
                values.get('partner_id'))
            if partner_id.user_id:
                self.user_id = partner_id.user_id.id
            if not partner_id.user_id:
                self.user_id = self.env.user

        return super(SaleOrder, self).write(values)

    def get_so_lines(self):
        """Function return sale order line."""
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'name': _('SO Lines'),
            'res_model': 'sale.order.line',
            'target': 'new',
            'domain': [('id', 'in', self.order_line.ids)],
        }

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        company_id = self.company_id.id
        journal_id = (self.env['account.invoice'].with_context(
            company_id=company_id or self.env.user.company_id.id).default_get(
            ['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(
                _('Please define an accounting sales journal for this company.'))
        vinvoice = self.env['account.invoice'].new(
            {'partner_id': self.partner_id.id, 'type': 'out_invoice'})
        # Get partner extra fields
        vinvoice._onchange_partner_id()
        invoice_vals = vinvoice._convert_to_write(vinvoice._cache)
        invoice_vals.update({
            'name': (self.client_order_ref or '')[:2000],
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
            'company_id': company_id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
        })
        return invoice_vals

    def _get_so_line_count(self):
        for so in self:
            so.so_line_count = len(so.order_line.ids)

    def _get_notes(self):
        for so in self:
            if so.note:
                so.notes = so.note[0:10] + "..."

    so_line_count = fields.Integer(string='SO Count',
                                   compute='_get_so_line_count')

    notes = fields.Text(string='Notes', compute='_get_notes')

    def express_checkout(self):
        """Function create and validate Do, Invoice."""
        if self.state != 'sale':
            # Delivery Creation and Validation
            self.action_confirm()
            delivery_obj = self.picking_ids.filtered(
                lambda x: x.state != 'cancel')
            if delivery_obj:
                # for order_line in self.order_line:
                [picking_line.update({
                    'quantity_done': picking_line.sale_line_id.product_uom_qty,
                }) for picking_line in delivery_obj.move_lines]
                delivery_obj.action_done()
            # Invoice Creation and Validation
            self.action_invoice_create()
            invoice_obj = self.env['account.invoice'].search(
                [('origin', '=', self.name), ('state', '!=', 'cancel')])
            if invoice_obj:
                invoice_obj.action_invoice_open()
                # Redirect to created Invoice
                action = self.env.ref('account.action_invoice_tree1').read()[0]
                if len(invoice_obj) == 1:
                    form_view = [(self.env.ref(
                        'account.invoice_form').id, 'form')]
                    if 'views' in action:
                        action['views'] = form_view + [
                            (state, view) for state, view in action[
                                'views'] if view != 'form']
                    else:
                        action['views'] = form_view
                    action['res_id'] = invoice_obj.id
                else:
                    action = {'type': 'ir.actions.act_window_close'}
                return action


class SaleOrderLine(models.Model):
    """Class Inherit for added some functionality."""

    _inherit = 'sale.order.line'

    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=0.0)

    @api.multi
    def write(self, values):
        """Messsage post when qty change."""
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            self.filtered(
                lambda r: float_compare(
                    r.product_uom_qty, values['product_uom_qty'],
                    precision_digits=precision) != 0)._update_line_quantity(
                values)
        for line in self:
            if 'price_unit' in values:
                line._update_line_values(values)
        return super(SaleOrderLine, self).write(values)

    def _update_line_values(self, values):
        orders = self.mapped('order_id')
        for order in orders:
            order_lines = self.filtered(lambda x: x.order_id == order)
            for lines in order_lines:
                price_unit = float_round(values['price_unit'], 3)
                print("\n\n price_unit", price_unit)
                msg = '<ul>'
                if values.get('price_unit') and lines.price_unit != (values['price_unit']):
                    msg += "<li> %s:" % (lines.product_id.display_name,)
                    msg += "<br/>" + _("Price") + ": %s -> %s <br/>" % (
                        lines.price_unit, (values['price_unit']),)
                    msg += "</ul>"
                    order.message_post(body=msg)

    @api.model
    def _get_purchase_price(self, pricelist, product, product_uom, date):
        """Function Ovveride to change margin price."""
        frm_cur = self.env.user.company_id.currency_id
        to_cur = pricelist.currency_id
        purchase_price = product.net_cost
        if product_uom != product.uom_id:
            purchase_price = product.uom_id._compute_price(
                purchase_price, product_uom)
        price = frm_cur._convert(
            purchase_price, to_cur,
            self.order_id.company_id or self.env.user.company_id,
            date or fields.Date.today(), round=False)
        return {'purchase_price': price}

    def _compute_margin(self, order_id, product_id, product_uom_id):
        """Function Ovveride to change margin price."""
        frm_cur = self.env.user.company_id.currency_id
        to_cur = order_id.pricelist_id.currency_id
        purchase_price = product_id.net_cost
        if product_uom_id != product_id.uom_id:
            purchase_price = product_id.uom_id._compute_price(
                purchase_price, product_uom_id)
        price = frm_cur._convert(
            purchase_price, to_cur, order_id.company_id or
            self.env.user.company_id,
            order_id.date_order or fields.Date.today(), round=False)
        return price

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            product_qty = self.product_uom._compute_quantity(
                self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.qty_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    message = _('You plan to sell %s %s of %s but you only have %s %s available in %s warehouse.') % \
                        (self.product_uom_qty, self.product_uom.name, self.product_id.name,
                         product.qty_available, product.uom_id.name, self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.qty_available, self.product_id.qty_available, precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available across all warehouses.\n\n') % \
                            (self.product_id.qty_available, product.uom_id.name)
                        for warehouse in self.env['stock.warehouse'].search([]):
                            quantity = self.product_id.with_context(
                                warehouse=warehouse.id).qty_available
                            if quantity > 0:
                                message += "%s: %s %s\n" % (
                                    warehouse.name, quantity,
                                    self.product_id.uom_id.name)
                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message': message
                    }
                    return {'warning': warning_mess}
        return {}

    @api.onchange('product_id')
    def product_id_change(self):

        """ 
            Method override for change product uom quantity by default 0 in So
            
        """

        if not self.product_id:
            return {'domain': {'product_uom': []}}

        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.attribute_value_id not in self.product_id.product_tmpl_id._get_valid_product_attribute_values():
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav.product_attribute_value_id not in self.product_id.product_tmpl_id._get_valid_product_attribute_values():
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            """
                commient this line for set product_uom_qty is 0.
            """
            # vals['product_uom_qty'] = self.product_uom_qty or 1.0
            vals['product_uom_qty'] = self.product_uom_qty or 0.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        name = self.get_sale_order_line_multiline_description_sale(product)

        vals.update(name=name)

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result