# -*- coding: utf-8 -*-

from odoo import fields, models


class DigitalSignature(models.TransientModel):
    """Class added to pass report details."""

    _name = 'digital.signature.wizard'
    _description = "Digital Signature Pad"

    digital_signature = fields.Binary('Signature', copy=False)

    def action_registered_sign(self):
        """Update signature in invoice."""
        active_id = self._context.get('active_id')
        invoice_obj = self.env['account.invoice'].browse(active_id)
        invoice_obj.write({
            'digital_signature': self.digital_signature,
            'has_to_be_signed': True
        })
