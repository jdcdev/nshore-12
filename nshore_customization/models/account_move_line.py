from odoo import api, fields, models, _


class AccountMove(models.Model):

    _name = "account.move"
    _inherit = ['account.move','mail.thread', 'mail.activity.mixin']



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def write(self, vals):
        """Messsage post when account_id update."""
        if 'account_id' in vals:
            for line in self:
                line._update_line_account(vals)
        if 'partner_id' in vals:
            for line in self:
                line._update_line_partner(vals)
        if 'name' in vals:
            for line in self:
                line._update_line_label(vals)
        if 'debit' and 'credit' in vals:
            for line in self:
                line._update_line_debit_credit(vals)
        return super(AccountMoveLine, self).write(vals)

    def _update_line_account(self, vals):
        """Fucntion call to add message in chatter when account_id change."""
        account_name = self.env['account.account'].browse(
            vals['account_id']
        )
        msg = "<b>The Move Line has been updated.</b><ul><br/> %s: %s -> %s <br/></ul>" % (
            _("Account"),
            self.account_id.display_name,
            account_name.display_name
        )
        self.move_id.message_post(body=msg)

    def _update_line_partner(self, vals):
        """Fucntion call to add message in chatter when partner_id change."""
        partner_name = self.env['res.partner'].browse(
            vals['partner_id']
        )
        msg = "<br/> %s: %s -> %s <br/></ul>" % (
            _("Partner"),
            self.partner_id.display_name,
            partner_name.display_name
        )
        self.move_id.message_post(body=msg)

    def _update_line_label(self, vals):
        # Function call to log when update Label
        move = self.mapped('move_id')
        for moves in move:
            move_lines = self.filtered(lambda x: x.move_id == move)
            for lines in move_lines:
                msg = '<ul>'
                if vals.get('name') and lines.credit != vals['name']:
                    msg += "<br/>" + _("Label") + ": %s -> %s <br/>" % (
                        lines.name, vals['name'],)
                    msg += "</ul>"
                    move.message_post(body=msg)

    def _update_line_debit_credit(self, vals):
        # Function call to log when update Prices
        move = self.mapped('move_id')
        for moves in move:
            move_lines = self.filtered(lambda x: x.move_id == move)
            for lines in move_lines:
                msg = '<ul>'
                if vals.get('credit') and lines.credit != float(vals['credit']):
                    msg += "<br/>" + _("Price") + ": %s -> %s <br/>" % (
                        lines.credit, float(vals['credit']),)
                    msg += "</ul>"
                    move.message_post(body=msg)



