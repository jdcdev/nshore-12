# -*- coding: utf-8 -*-

from odoo import models, fields
import csv
from datetime import date
import io
import base64


class InvoiceList(models.TransientModel):
    """Model create for create Journal Entries."""

    _name = 'opening.bal.script'

    file_slect = fields.Binary(string="Select Excel File")

    def update_opening_bal(self):
        """Function call to update opening balance."""
        csv_data = base64.b64decode(self.file_slect)
        keys = ['External ID', 'CurrentBalance']
        data_file = io.StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        values = {}
        csv_reader = csv.reader(data_file, delimiter=',')
        file_reader.extend(csv_reader)
        move_line_1 = {}
        move_line_2 = {}
        account_account = self.env['account.account']
        for i in range(len(file_reader)):
            if i == 0:
                continue
            else:
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))
                partner = self.env['res.partner'].search(
                    [('ref', '=', values['External ID'])])
                current_bal = float(values['CurrentBalance'])
                # minus entries value
                if current_bal < 0:
                    move_line_1 = {
                        'partner_id': partner.id,
                        'account_id': account_account.search(
                            [('code', '=', 30000)]).id,
                        'debit': abs(float(current_bal)),
                        'credit': 0}
                    move_line_2 = {
                        'partner_id': partner.id,
                        'account_id': account_account.search(
                            [('code', '=', 1200)]).id,
                        'debit': 0,
                        'credit': abs(float(current_bal))}
                # Plus entries value
                else:
                    move_line_1 = {
                        'partner_id': partner.id,
                        'account_id': account_account.search(
                            [('code', '=', 30000)]).id,
                        'debit': 0,
                        'credit': float(current_bal)}
                    move_line_2 = {
                        'partner_id': partner.id,
                        'account_id': account_account.search(
                            [('code', '=', 1200)]).id,
                        'debit': float(current_bal),
                        'credit': 0}
                move = self.env['account.move'].create({
                    'date': date.today(),
                    'ref': partner.name,
                    'journal_id': 4,
                    'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)]})
                # move.action_post()
