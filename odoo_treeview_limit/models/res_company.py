# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    """Class Inherit to add tree view limit."""

    _inherit = "res.company"

    tree_limit = fields.Integer("Tree Limit", defualt=200000)
