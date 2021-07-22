from odoo import api, fields, models, _


class PortalWizard(models.TransientModel):
    """Class inherit to add log note for portal."""

    _inherit = 'portal.wizard'


    @api.multi
    def action_apply(self):
        res = super(PortalWizard, self).action_apply()
        names = self.user_ids.filtered(lambda x: x.in_portal).mapped('partner_id').mapped('display_name')
        msg = """
                %s Granted Poratl Access to:<br/>
                <ul>%s</ul>""" % (self.env.user.name, ''.join(["<li>%s</li>" % x for x in names]))
        active_ids = self._context.get('active_ids')
        user = self.env['res.partner'].browse(active_ids)
        user.message_post(body=msg)
        return res 
