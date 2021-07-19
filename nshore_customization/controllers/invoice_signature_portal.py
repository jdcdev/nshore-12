# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.portal.controllers.mail import _message_post_helper


class PortalAccount(CustomerPortal):

    @http.route(['/my/invoices/<int:order_id>/accept'], type='json', auth="public", website=True)
    def portal_invoice_accept(self, res_id, access_token=None, partner_name=None, signature=None, order_id=None):
        try:
            invoice_sudo = self._document_check_access(
                'account.invoice', res_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid Invoice')}

        if not invoice_sudo.state != 'draft':
            return {'error': _('The Invoice is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}
        if not invoice_sudo.has_to_be_signed:
            invoice_sudo.digital_signature = signature
            invoice_sudo.signed_by = partner_name
            invoice_sudo.has_to_be_signed = True

        pdf = request.env.ref('account.account_invoices').sudo().render_qweb_pdf(
            [invoice_sudo.id])[0]
        _message_post_helper(
            res_model='account.invoice',
            res_id=invoice_sudo.id,
            message=_('Invoice signed by %s') % (partner_name,),
            attachments=[('%s.pdf' % invoice_sudo.name, pdf)],
            **({'token': access_token} if access_token else {}))

        return {
            'force_refresh': True,
            'redirect_url': invoice_sudo.get_portal_url(
                query_string='&message=sign_ok'),
        }
