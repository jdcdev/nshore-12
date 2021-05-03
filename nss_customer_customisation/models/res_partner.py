from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    default_delivery = fields.Boolean("Default delivery Address?")

    @api.onchange('default_delivery')
    def _onchange_default_invoice(self):
        if self.default_invoice:
            if self.parent_id:
                res_partner = self.parent_id
                if res_partner.child_ids and any([partner.default_delivery == True for partner in res_partner.child_ids]):
                    raise ValidationError(
                        """ There is one default invoice address. """)
