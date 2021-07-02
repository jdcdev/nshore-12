# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PricelistItem(models.Model):
    """Class inherit to add field."""

    _inherit = "product.pricelist.item"
    _order = 'name asc'

    base = fields.Selection(selection_add=[('net_cost', 'Net Cost')])
    name = fields.Char(
        'Name', compute='_get_pricelist_item_name_price',
        help="Explicit rule name for this pricelist line.", store=True)
    old_fixed_price = fields.Float(string="Old Fixed")
    price_discount = fields.Float('Price Discount', default=0, digits=(16, 6))

    @api.multi
    def write(self, values):
        """Messsage post when qty change."""
        if 'fixed_price' or 'product_tmpl_id' or 'product_id' or 'percent_price' or 'applied_on' or 'compute_price' or 'base_pricelist_id' or 'base' or 'price_discount' in values:
            for line in self:
                line._update_line_quantity(values)
        return super(PricelistItem, self).write(values)

    def _update_line_quantity(self, values):
        """Fucntion call to add message in chatter when qty change."""
        pricelist = self.mapped('pricelist_id')
        for plist in pricelist:
            pricelist_item = self.filtered(lambda x: x.pricelist_id == plist)
            msg = "<ul>"
            for item in pricelist_item:
                if values.get('product_tmpl_id') and item.product_tmpl_id.id != values.get('product_tmpl_id'):
                    product_tmpl = self.env['product.template'].browse(
                        values['product_tmpl_id'])
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Apply On Product") + ": %s -> %s <br/>" % (
                        item.product_tmpl_id.name, product_tmpl.name,)
                    plist.message_post(body=msg)
                if values.get('product_id') and item.product_id.id != values.get('product_id'):
                    product = self.env['product.product'].browse(
                        values['product_id'])
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Apply On Product Variant") + ": %s -> %s <br/>" % (
                        item.product_id.name, product.name,)
                    plist.message_post(body=msg)
                if values.get('applied_on') and item.applied_on != values.get('applied_on'):
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Applied On") + ": %s -> %s <br/>" % (
                        item.applied_on, values.get('applied_on'),)
                    plist.message_post(body=msg)
                if values.get('compute_price') and item.compute_price != values.get('compute_price'):
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Compute Price") + ": %s -> %s <br/>" % (
                        item.compute_price, values.get('compute_price'),)
                    plist.message_post(body=msg)
                if values.get('percent_price') and item.percent_price != values.get('percent_price'):
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Percentage Price") + ": %s -> %s <br/>" % (
                        item.percent_price, values.get('percent_price'),)
                    plist.message_post(body=msg)
                if values.get('base') and item.base != values.get('base'):
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Based on") + ": %s -> %s <br/>" % (
                        item.base, values.get('base'),)
                    plist.message_post(body=msg)
                if values.get('price_discount') and item.price_discount != values.get('price_discount'):
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Price Discount") + ": %s -> %s <br/>" % (
                        item.price_discount, values.get('price_discount'),)
                    plist.message_post(body=msg)
                if values.get('base_pricelist_id') and item.base_pricelist_id != values.get('base_pricelist_id'):
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Other Pricelist") + ": %s -> %s <br/>" % (
                        item.base_pricelist_id, values.get('base_pricelist_id'),)
                    plist.message_post(body=msg)
                if values.get('fixed_price') and item.fixed_price != values.get('fixed_price'):
                    msg += "<li> %s:" % (item.name,)
                    msg += "<br/>" + _("Fixed Price") + ": %s -> %s <br/>" % (
                        item.fixed_price, values.get('fixed_price'),)
                    plist.message_post(body=msg)

class Pricelist(models.Model):
    """Class Inherit to added name serach for limit."""

    _name = "product.pricelist"
    _inherit = ['product.pricelist', 'mail.thread', 'mail.activity.mixin']


    @api.model
    def _name_search(
            self, name, args=None, operator='ilike', limit=100,
            name_get_uid=None):
        return super(Pricelist, self)._name_search(
            name, args, operator=operator, limit=25000,
            name_get_uid=name_get_uid)
