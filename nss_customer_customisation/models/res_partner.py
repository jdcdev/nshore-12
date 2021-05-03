from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    default_delivery = fields.Boolean("Default delivery Address?")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        if self._context.get('is_company'):
            domain = [('is_company', '=', True)]
            account_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
            return self.browse(account_ids).name_get()
        return super(ResPartner, self)._name_search(name, args, operator=operator, limit=limit,
                                                    name_get_uid=name_get_uid)

    @api.onchange('default_delivery')
    def _onchange_default_invoice(self):
        if self.default_delivery:
            if self.parent_id:
                res_partner = self.parent_id
                default_delivery = res_partner.child_ids.filtered(lambda x: x.default_delivery == True)
                if res_partner.child_ids and len(default_delivery) > 1:
                    raise ValidationError(
                        """ There is one default shipping address. """)
