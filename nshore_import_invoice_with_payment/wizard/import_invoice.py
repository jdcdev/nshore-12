# -*- coding: utf-8 -*-

import mimetypes
import base64
import xlrd
import os
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvoicePaymentWizard(models.TransientModel):
    _name = "import.invoice.payment"

    name = fields.Char()
    csv_file = fields.Binary(string="Open File")

    @api.multi
    def action_update_products(self):
        for rec in self:
            product_list = []
            mimetypes_list = [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            if not rec.name:
                raise UserError(_("Please upload file."))
            mime_type = mimetypes.guess_type(rec.name)
            if mime_type[0] in mimetypes_list:
                with open(os.path.expanduser('/tmp/product_data.csv'), 'wb') as fout:
                    fout.write(base64.decodestring(rec.csv_file))
                workbook = xlrd.open_workbook('/tmp/product_data.csv')
                worksheet = workbook.sheet_by_index(0)
                nrows = worksheet.nrows
                print("\n\nnrows\t", nrows, "\n\n")
                ModelData = self.env['ir.model.data']
                AccountPayment = self.env['account.payment']
                AccountInvoice = self.env['account.invoice']

                for row_idx in range(1, nrows):
                    invoice_external_id = str(worksheet.cell(row_idx, 2).value)
                    payment_external_id = int(worksheet.cell(row_idx, 3).value)
                    model_invoice_id = ModelData.search([('name', '=', invoice_external_id),('model','=', 'account.invoice')])
                    model_payment_id = ModelData.search([('name', '=', payment_external_id),('model','=', 'account.payment')])
                    if model_payment_id and model_invoice_id:
                        invoice = AccountInvoice.browse(model_invoice_id.res_id)
                        payment = AccountPayment.browse(model_payment_id.res_id)
                        if payment.state == 'draft':
                            payment.post()
                        if invoice not in payment.invoice_ids:
                            self._cr.execute("""INSERT INTO account_invoice_payment_rel (invoice_id, payment_id) VALUES (%s, %s)""", (invoice.id, payment.id))
                            """ Reconcile payable/receivable lines from the invoice with payment_line """
                            payment_line = payment.move_line_ids.filtered(lambda x: x.account_id.reconcile)
                            invoice.register_payment(payment_line)
            else:
                raise UserError(_("Please upload an excel file."))
