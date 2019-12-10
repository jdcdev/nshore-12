from odoo import api, models, fields
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
    date_invoice = fields.Date(string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False, default=fields.Date.today())

    @api.multi
    def action_invoice_open(self):
        for order in self:
            partner = self.partner_id
            total_money = partner.credit - self.amount_total
            if not partner.allow_supervisor and (partner.credit + self.amount_total) > partner.credit_limit and not partner.over_credit:
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
