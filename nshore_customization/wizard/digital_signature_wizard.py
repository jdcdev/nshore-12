# -*- coding: utf-8 -*-

from odoo import fields, models, api


class DigitalSignature(models.TransientModel):
    """Class added to pass report details."""

    _name = 'digital.signature.wizard'
    _description = "Digital Signature Pad"

    name = fields.Char('Name')
    digital_signature = fields.Binary('Signature', copy=False)

    @api.model
    def create(self, vals):
        """Function call to pass signature into invoice."""
        res = super(DigitalSignature, self).create(vals)
        active_id = self._context.get('id')
        invoice_obj = self.env['account.invoice'].browse(active_id)
        invoice_obj.write({
            'digital_signature': res.digital_signature,
            'has_to_be_signed': True
        })
        res.name = 'Signature_of_' + invoice_obj.partner_id.name
        return res
