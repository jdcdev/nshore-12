from odoo import fields, models, _, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Class Inherit for added some functionality."""

    _inherit = 'sale.order'

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

    so_line_count = fields.Integer(string='SO Count',
                                   compute='_get_so_line_count')

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
