from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    default_delivery = fields.Boolean("Default delivery Address?")

    @api.onchange('default_delivery')
    def _onchange_default_invoice(self):
        if self.default_delivery:
            if self.parent_id:
                res_partner = self.parent_id
                default_delivery = res_partner.child_ids.filtered(lambda x: x.default_delivery == True)
                if res_partner.child_ids and len(default_delivery) > 1:
                    raise ValidationError(
                        """ There is one default invoice address. """)
