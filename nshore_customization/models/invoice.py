from odoo import api, models, fields, _
from odoo.http import request


class CustomPopMessage(models.TransientModel):
    _name = "custom.pop.message"

    _description = 'Custom Pop Message'

    message = fields.Html('Message')
    user_name = fields.Char('User Name')
    password = fields.Char('Password')
    error = fields.Html('Error')
    invoice = fields.Many2one('account.invoice')
    allow_supervisor = fields.Boolean('Allow Supervisor', default=False)

    @api.multi
    def approve_over_limit(self):
        self.allow_supervisor = True
        view = self.env.ref(
            'nshore_customization.custom_pop_message_wizard_view_form')
        return {
            'name': 'Supervisor Sign In',
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_model': 'custom.pop.message',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def display_error(self, error):
        self.error = error
        return self.approve_over_limit()

    @api.multi
    def signin_supervisor(self):
        Users = self.env['res.users']  # type: object
        supervisor = Users.search([('login', '=', self.user_name)])
        error = "<p style='font-size: 15px;color: red;'> * You don't have rights to validate over due invoice.</p>"
        if supervisor:
            flag = supervisor.has_group(
                'nshore_customization.group_is_supervisor')
            if flag:
                user_id = Users._login(
                    request.session.db, self.user_name, self.password)
                if user_id:
                    self.invoice.partner_id.write({'allow_supervisor': True})
                    self.invoice.write({'validated_by': user_id})
                    self.invoice.action_invoice_open()
                    self.invoice.partner_id.write({'allow_supervisor': False})
                else:
                    error = "<p style='font-size: 15px;color: red;'> * Invalid User Name/Password.</p>"
                    return self.display_error(error)
            else:
                return self.display_error(error)
        else:
            return self.display_error(error)

        return False


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    validated_by = fields.Many2one(
        'res.users', string="Validated By", track_visibility='always')
    date_invoice = fields.Date(
        string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False, default=fields.Date.today())
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist',
        readonly=True, states={'draft': [('readonly', False)]})
    user_id = fields.Many2one('res.users', readonly=False)
    invoice_line_ids = fields.One2many(
        'account.invoice.line', 'invoice_id',
        string='Invoice Lines', oldname='invoice_line', copy=True)

    # def price_updates(self):
    #     """Update products prices when change the partner."""
    #     for line in self.invoice_line_ids:
    #         line._onchange_product_id()

    @api.multi
    def action_invoice_open(self):
        for order in self:
            partner = self.partner_id
            total_money = partner.credit - self.amount_total
            if not partner.allow_supervisor and (
                    partner.credit + self.amount_total) > partner.credit_limit and not partner.over_credit:
                msg = 'Can not validate Invoice, Total outstanding Amount ' \
                      '<b> %s </b> ! <br/> \n' % (
                          '${:,.2f}'.format(total_money))

                view = self.env.ref(
                    'nshore_customization.custom_pop_message_wizard_view_form')
                return {
                    'name': 'Warning',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_model': 'custom.pop.message',
                    'target': 'new',
                    'context': {'default_message': msg, 'default_invoice': order.id}
                }
            else:
                return super(AccountInvoice, self).action_invoice_open()

    @api.onchange('partner_id')
    def onchange_partner(self):
        """Onchange call for customer pricelist."""
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
        }
        self.update(values)


class AccountInvoiceLine(models.Model):
    """Account Invoice Line Inherit for pricelist,create modification."""

    _inherit = "account.invoice.line"

    product_net_cost = fields.Float('Product Net Cost')
    product_list_price = fields.Float('Product Sales Price')
    # new_price = fields.Boolean("New Price")

    @api.multi
    def write(self, values):
        """Messsage post when qty change."""
        if 'quantity' or 'product_net_cost' or 'product_list_price' in values:
            for line in self:
                line._update_line_values(values)
        return super(AccountInvoiceLine, self).write(values)

    def _update_line_values(self, values):
        """Fucntion call to add message in chatter when qty change."""
        invoice = self.mapped('invoice_id')
        for inv in invoice:
            inv_lines = self.filtered(lambda x: x.invoice_id == invoice)
            msg = '<ul>'
            for lines in inv_lines:
                if values.get('quantity'):
                    msg += "<li> %s:" % (lines.product_id.display_name,)
                    msg += "<br/>" + _("Quantity") + ": %s -> %s <br/>" % (
                        lines.quantity, float(values['quantity']),)
                if values.get('product_net_cost'):
                    msg += "<li> %s:" % (lines.product_id.display_name,)
                    msg += "<br/>" + _("Net Cost") + ": %s -> %s <br/>" % (
                        lines.product_net_cost, float(values['product_net_cost']),)
                if values.get('product_list_price'):
                    msg += "<li> %s:" % (lines.product_id.display_name,)
                    msg += "<br/>" + _("Sales Price") + ": %s -> %s <br/>" % (
                        lines.product_list_price, float(values['product_list_price']),)
            invoice.message_post(body=msg)

    @api.model_create_multi
    def create(self, vals_list):
        """Create override to update name."""
        for vals in vals_list:
            # if not vals.get('new_price'):
            #     vals.update({'new_price': True})
            if vals.get('name') is False:
                vals_list = [i for i in vals_list if not (i['name']is False)]
        return super(AccountInvoiceLine, self).create(vals_list)

    @api.multi
    def _get_display_price(self, product):
        """Function to set product's unit price as per pricelist."""
        if self.invoice_id.partner_id.id:
            if self.invoice_id.pricelist_id.discount_policy == 'with_discount':
                return product.with_context(
                    pricelist=self.invoice_id.pricelist_id.id).price
            product_context = dict(
                self.env.context, partner_id=self.invoice_id.partner_id.id,
                date=self.invoice_id.date_invoice,
                uom=self.product_id.uom_id.id)
            final_price, rule_id = self.invoice_id.pricelist_id.with_context(
                product_context).get_product_price_rule(
                self.product_id, self.qty or 1.0, self.invoice_id.partner_id)
            base_price, currency = self.with_context(
                product_context)._get_real_price_currency(
                product, rule_id, self.qty, self.product_id.uom_id,
                self.invoice_id.pricelist_id.id)
            if currency != self.invoice_id.pricelist_id.currency_id:
                base_price = currency._convert(
                    base_price, self.invoice_id.pricelist_id.currency_id,
                    self.invoice_id.company_id or self.env.user.company_id,
                    self.invoice_id.date_invoice or fields.Date.today())
            return max(base_price, final_price)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        type = self.invoice_id.type

        if not part:
            warning = {
                'title': _('Warning!'),
                'message': _('You must first select a partner.'),
            }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
            if fpos:
                self.account_id = fpos.map_account(self.account_id)
        else:
            self.product_net_cost = self.product_id.net_cost
            self.product_list_price = self.product_id.lst_price
            # self.update({'new_price': True})
            self_lang = self
            if part.lang:
                self_lang = self.with_context(lang=part.lang)

            product = self_lang.product_id
            account = self.get_invoice_line_account(
                type, product, fpos, company)
            if account:
                self.account_id = account.id
            self._set_taxes()

            product_name = self_lang._get_invoice_line_name_from_product()
            if product_name != None:
                self.name = product_name

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [
                ('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:
                if not self.invoice_id.pricelist_id:
                    if self.uom_id and self.uom_id.id != product.uom_id.id:
                        self.price_unit = product.uom_id._compute_price(
                            self.price_unit, self.uom_id)
                if self.invoice_id.pricelist_id and self.invoice_id.partner_id:
                    self.price_unit = self.env[
                        'account.tax']._fix_tax_included_price_company(
                            self._get_display_price(product),
                            product.taxes_id, self.invoice_line_tax_ids,
                            self.company_id)
        return {'domain': domain}

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        warning = {}
        result = {}
        if not self.uom_id:
            self.price_unit = 0.0

        if self.product_id and self.uom_id:
            self._set_taxes()
            if not self.invoice_id.pricelist_id:
                self.price_unit = self.product_id.uom_id._compute_price(
                    self.price_unit, self.uom_id)
            if self.invoice_id.pricelist_id and self.invoice_id.partner_id:
                product = self.product_id.with_context(
                    lang=self.invoice_id.partner_id.lang,
                    partner=self.invoice_id.partner_id,
                    quantity=self.quantity,
                    date=self.invoice_id.date_invoice,
                    pricelist=self.invoice_id.pricelist_id.id,
                    uom=self.uom_id.id,
                    fiscal_position=self.env.context.get('fiscal_position'))
                self.price_unit = self.env[
                    'account.tax']._fix_tax_included_price_company(
                        self._get_display_price(product), product.taxes_id,
                        self.invoice_line_tax_ids, self.company_id)
            if self.product_id.uom_id.category_id.id != self.uom_id.category_id.id:
                warning = {
                    'title': _('Warning!'),
                    'message': _('The selected unit of measure has to be in the same category as the product unit of measure.'),
                }
                self.uom_id = self.product_id.uom_id.id
        if warning:
            result['warning'] = warning
        return result
