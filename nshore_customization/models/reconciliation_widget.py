# -*- coding: utf-8 -*-

from odoo import api, models


class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def get_data_for_manual_reconciliation(self, res_type, res_ids=None, account_type=None):
        """Override: to set order based on partner name
        Added only Partner Name in to order by query.
        """

        Account = self.env['account.account']
        Partner = self.env['res.partner']

        if res_ids is not None and len(res_ids) == 0:
            # Note : this short-circuiting is better for performances, but also required
            # since postgresql doesn't implement empty list (so 'AND id in ()' is useless)
            return []
        res_ids = res_ids and tuple(res_ids)

        assert res_type in ('partner', 'account')
        assert account_type in ('payable', 'receivable', None)
        is_partner = res_type == 'partner'
        res_alias = is_partner and 'p' or 'a'
        aml_ids = self._context.get('active_ids') and self._context.get('active_model') == 'account.move.line' and tuple(self._context.get('active_ids'))

        query = ("""
            SELECT {0} account_id, account_name, account_code, max_date,
                   to_char(last_time_entries_checked, 'YYYY-MM-DD') AS last_time_entries_checked
            FROM (
                    SELECT {1}
                        {res_alias}.last_time_entries_checked AS last_time_entries_checked,
                        a.id AS account_id,
                        a.name AS account_name,
                        a.code AS account_code,
                        MAX(l.write_date) AS max_date
                    FROM
                        account_move_line l
                        RIGHT JOIN account_account a ON (a.id = l.account_id)
                        RIGHT JOIN account_account_type at ON (at.id = a.user_type_id)
                        {2}
                    WHERE
                        a.reconcile IS TRUE
                        AND l.full_reconcile_id is NULL
                        {3}
                        {4}
                        {5}
                        AND l.company_id = {6}
                        AND EXISTS (
                            SELECT NULL
                            FROM account_move_line l
                            JOIN account_move move ON move.id = l.move_id
                            JOIN account_journal journal ON journal.id = move.journal_id
                            WHERE l.account_id = a.id
                            {7}
                            AND (move.state = 'posted' OR (journal.post_at_bank_rec AND move.state = 'draft'))
                            AND l.amount_residual > 0
                        )
                        AND EXISTS (
                            SELECT NULL
                            FROM account_move_line l
                            JOIN account_move move ON move.id = l.move_id
                            JOIN account_journal journal ON journal.id = move.journal_id
                            WHERE l.account_id = a.id
                            {7}
                            AND (move.state = 'posted' OR (journal.post_at_bank_rec AND move.state = 'draft'))
                            AND l.amount_residual < 0
                        )
                        {8}
                    GROUP BY {9} a.id, a.name, a.code, {res_alias}.last_time_entries_checked
                    ORDER BY {10} {res_alias}.last_time_entries_checked
                ) as s
            WHERE (last_time_entries_checked IS NULL OR max_date > last_time_entries_checked)
        """.format(
            is_partner and 'partner_id, partner_name,' or ' ',
            is_partner and 'p.id AS partner_id, p.name AS partner_name,' or ' ',
            is_partner and 'RIGHT JOIN res_partner p ON (l.partner_id = p.id)' or ' ',
            is_partner and ' ' or "AND at.type <> 'payable' AND at.type <> 'receivable'",
            account_type and "AND at.type = %(account_type)s" or '',
            res_ids and 'AND ' + res_alias + '.id in %(res_ids)s' or '',
            self.env.user.company_id.id,
            is_partner and 'AND l.partner_id = p.id' or ' ',
            aml_ids and 'AND l.id IN %(aml_ids)s' or '',
            is_partner and 'l.partner_id, p.id,' or ' ',
            is_partner and 'partner_name ASC,' or '',
            res_alias=res_alias
        ))
        self.env.cr.execute(query, locals())

        # Apply ir_rules by filtering out
        rows = self.env.cr.dictfetchall()
        ids = [x['account_id'] for x in rows]
        allowed_ids = set(Account.browse(ids).ids)
        rows = [row for row in rows if row['account_id'] in allowed_ids]
        if is_partner:
            ids = [x['partner_id'] for x in rows]
            allowed_ids = set(Partner.browse(ids).ids)
            rows = [row for row in rows if row['partner_id'] in allowed_ids]

        # Keep mode for future use in JS
        if res_type == 'account':
            mode = 'accounts'
        else:
            mode = 'customers' if account_type == 'receivable' else 'suppliers'

        # Fetch other data
        for row in rows:
            account = Account.browse(row['account_id'])
            currency = account.currency_id or account.company_id.currency_id
            row['currency_id'] = currency.id
            partner_id = is_partner and row['partner_id'] or None
            rec_prop = aml_ids and self.env['account.move.line'].browse(aml_ids) or self._get_move_line_reconciliation_proposition(account.id, partner_id)
            row['reconciliation_proposition'] = self._prepare_move_lines(rec_prop, target_currency=currency)
            row['mode'] = mode
            row['company_id'] = account.company_id.id
        # Return the partners with a reconciliation proposition first, since they are most likely to
        # be reconciled.
        return [r for r in rows if r['reconciliation_proposition']] + [r for r in rows if not r['reconciliation_proposition']]
